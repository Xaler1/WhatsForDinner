import os
import json
import torch

import sys

# move to the devit directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "./devit"))

torch.set_grad_enabled(False)
import numpy as np
from detectron2.config import get_cfg
import detectron2.data.transforms as T
import detectron2.data.detection_utils as utils
from tools.train_net import Trainer, DetectionCheckpointer

# move back
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torchvision.transforms.functional import to_pil_image

import seaborn as sns
import torchvision.ops as ops
from torchvision.ops import box_area, box_iou
import random

from PIL import Image, ImageColor, ImageDraw, ImageFont
import gc

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# Adapted from the devit demo
class VegetableVision:
    def __init__(
            self,
            config_file="./configs/open-vocabulary/lvis/vitl.yaml",
            rpn_config_file="./configs/RPN/mask_rcnn_R_50_FPN_1x.yaml",
            model_path="./weights/trained/open-vocabulary/lvis/vitl_0069999.pth",
            output_dir='output',
            category_space="ycb_prototypes.pth",
            topk=1,
            threshold=0.7
    ):
        os.makedirs(output_dir, exist_ok=True)

        # Get absolute path
        category_space = os.path.join(os.path.dirname(__file__), category_space)
        os.chdir("./devit")

        self.threshold = threshold

        self.cfg = get_cfg()
        self.cfg.merge_from_file(config_file)
        self.cfg.DE.OFFLINE_RPN_CONFIG = rpn_config_file
        self.cfg.DE.TOPK = topk
        self.cfg.MODEL.MASK_ON = True
        self.cfg.freeze()

        self.augs = utils.build_augmentation(self.cfg, False)
        self.augs = T.AugmentationList(self.augs)

        self.model = Trainer.build_model(self.cfg).to(device)
        self.model.load_state_dict(torch.load(model_path, map_location=device)['model'])
        self.model.eval()
        self.model = self.model.to(device)
        category_space = torch.load(category_space)
        self.model.label_names = category_space['label_names']
        self.model.test_class_weight = category_space['prototypes'].to(device)
        self.label_names = self.model.label_names

        os.chdir("..")

    def filter_boxes(self, instances, threshold=0.0):
        indexes = instances.scores >= threshold
        assert indexes.sum() > 0
        boxes = instances.pred_boxes.tensor[indexes, :]
        pred_classes = instances.pred_classes[indexes]
        return boxes, pred_classes, instances.scores[indexes]

    def assign_colors(self, pred_classes, label_names, seed=1):
        all_classes = torch.unique(pred_classes).tolist()
        all_classes = list(set([label_names[ci] for ci in all_classes]))
        colors = list(sns.color_palette("hls", len(all_classes)).as_hex())
        random.seed(seed)
        random.shuffle(colors)
        class2color = {}
        for cname, hx in zip(all_classes, colors):
            class2color[cname] = hx
        colors = [class2color[label_names[cid]] for cid in pred_classes.tolist()]
        return colors

    def draw_boxes(
            self,
            image: torch.Tensor,
            boxes: torch.Tensor,
            labels: list[str],
            colors
    ):
        num_boxes = boxes.shape[0]

        font_size = int(48.0 / 4000 * np.max(image.shape[:2]) + 5)
        width = int(10.0 / 4000 * np.max(image.shape[:2]) + 2)
        if num_boxes == 0:
            return image

        colors = [(ImageColor.getrgb(color) if isinstance(color, str) else color) for color in colors]

        txt_font = ImageFont.truetype(font="arial.ttf", size=font_size)

        ndarr = image.permute(1, 2, 0).cpu().numpy()
        img_to_draw = Image.fromarray(ndarr)
        img_boxes = boxes.to(torch.int64).tolist()

        draw = ImageDraw.Draw(img_to_draw)

        for bbox, color, label in zip(img_boxes, colors, labels):  # type: ignore[arg-type]
            draw.rectangle(bbox, width=width, outline=color)

            textbbox = draw.textbbox((bbox[0], bbox[1]), label, font=txt_font)

            draw.rectangle(textbbox, fill="black")
            draw.text((bbox[0], bbox[1]), label, fill=color, font=txt_font)

        return torch.from_numpy(np.array(img_to_draw)).permute(2, 0, 1).to(dtype=torch.uint8)

    def get_ingredients(self, img_file, output_file):
        gc.collect()
        torch.cuda.empty_cache()

        dataset_dict = {}
        image = utils.read_image(img_file, format="RGB")
        dataset_dict["height"], dataset_dict["width"] = image.shape[0], image.shape[1]

        aug_input = T.AugInput(image)
        self.augs(aug_input)
        dataset_dict["image"] = torch.as_tensor(np.ascontiguousarray(aug_input.image.transpose(2, 0, 1))).to(device)

        batched_inputs = [dataset_dict]

        output = self.model(batched_inputs)[0]
        output['label_names'] = self.model.label_names

        instances = output['instances']
        boxes, pred_classes, scores = self.filter_boxes(instances, threshold=self.threshold)

        mask = box_area(boxes) >= 400
        boxes = boxes[mask]
        pred_classes = pred_classes[mask]
        scores = scores[mask]
        mask = ops.nms(boxes, scores, 0.3)
        boxes = boxes[mask].cpu()
        pred_classes = pred_classes[mask]
        indexes = list(range(len(pred_classes)))
        for c in torch.unique(pred_classes).tolist():
            box_id_indexes = (pred_classes == c).nonzero().flatten().tolist()
            for i in range(len(box_id_indexes)):
                for j in range(i + 1, len(box_id_indexes)):
                    bid1 = box_id_indexes[i]
                    bid2 = box_id_indexes[j]
                    arr1 = boxes[bid1].numpy()
                    arr2 = boxes[bid2].numpy()
                    a1 = np.prod(arr1[2:] - arr1[:2])
                    a2 = np.prod(arr2[2:] - arr2[:2])
                    top_left = np.maximum(arr1[:2], arr2[:2])  # [[x, y]]
                    bottom_right = np.minimum(arr1[2:], arr2[2:])  # [[x, y]]
                    wh = bottom_right - top_left
                    ia = wh[0].clip(0) * wh[1].clip(0)
                    if ia >= 0.9 * min(a1, a2):  # same class overlapping case, and larger one is much larger than small
                        if a1 >= a2:
                            if bid2 in indexes:
                                indexes.remove(bid2)
                        else:
                            if bid1 in indexes:
                                indexes.remove(bid1)

        colors = self.assign_colors(pred_classes, self.model.label_names, seed=4)
        labels = [self.label_names[cid] for cid in pred_classes.tolist()]
        output = to_pil_image(self.draw_boxes(
            torch.as_tensor(image).permute(2, 0, 1),
            boxes,
            labels,
            colors
        ))
        output.save(output_file)
        gc.collect()
        torch.cuda.empty_cache()
        return labels


vision = VegetableVision()

while True:
    inputs = os.listdir("./input")
    for i in inputs:
        print("Found new image", i)
        img_file = f"./input/{i}"
        output_file = f"./output/{i}"
        ingredients = vision.get_ingredients(img_file, output_file)
        with open(f"./output/{i}".replace(".jpg", ".txt"), "w") as f:
            f.write("&".join(ingredients))
        os.remove(img_file)
