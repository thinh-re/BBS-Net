from typing import Dict, Optional, Tuple

import numpy as np
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL.Image import Image
from torch import Tensor
from transformers.image_processing_utils import BaseImageProcessor


# from transformers import VideoMAEImageProcessor, ViTImageProcessor
# See VideoMAEImageProcessor, ViTImageProcessor for more examples
class BBSNetImagePreProcessor(BaseImageProcessor):
    model_input_names = ["bbsnet_preprocessor"]

    def __init__(self, testsize: Optional[int] = 352, **kwargs) -> None:
        super().__init__(**kwargs)
        self.testsize = testsize
        self.rgb_transform = transforms.Compose(
            [
                transforms.Resize((self.testsize, self.testsize)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        self.gt_transform = transforms.ToTensor()
        # self.gt_transform = transforms.Compose([
        #     transforms.Resize((self.trainsize, self.trainsize)),
        #     transforms.ToTensor()])
        self.depth_transform = transforms.Compose(
            [transforms.Resize((self.testsize, self.testsize)), transforms.ToTensor()]
        )

    def preprocess(
        self,
        inputs: Dict[str, Image],  # {'rgb': ..., 'gt': ..., 'depth': ...}
        **kwargs
    ) -> Dict[str, Tensor]:
        rs = dict()
        if "rgb" in inputs:
            rs["rgb"] = self.rgb_transform(inputs["rgb"]).unsqueeze(0)
        if "gt" in inputs:
            rs["gt"] = self.gt_transform(inputs["gt"]).unsqueeze(0)
        if "depth" in inputs:
            rs["depth"] = self.depth_transform(inputs["depth"]).unsqueeze(0)
        return rs

    def postprocess(
        self, logits: Tensor, size: Tuple[int, int], **kwargs
    ) -> np.ndarray:
        logits: Tensor = F.upsample(
            logits, size=size, mode="bilinear", align_corners=False
        )
        res: np.ndarray = logits.sigmoid().squeeze().data.cpu().numpy()
        res = (res - res.min()) / (res.max() - res.min() + 1e-8)
        return res
