"""
Modify the original file to make the class support feature extraction
"""

import torch.nn as nn
import math
import torch.utils.model_zoo as model_zoo

model_urls = {
    'resnet18': 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
    'resnet34': 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
    'resnet50': 'https://download.pytorch.org/models/resnet50-19c8e357.pth',
    'resnet101': 'https://download.pytorch.org/models/resnet101-5d3b4d8f.pth',
    'resnet152': 'https://download.pytorch.org/models/resnet152-b121ed2d.pth',
}


def conv1x3x3(in_planes, out_planes, stride=1, t_stride=1):
    """1x3x3 convolution with padding"""
    return nn.Conv3d(in_planes, out_planes, kernel_size=(1, 3, 3),
                     stride=(t_stride, stride, stride),
                     padding=(0, 1, 1), bias=False)

def conv3x1x1(in_planes, out_planes, stride=1, t_stride=1):
    """3x1x1 convolution with padding"""
    return nn.Conv3d(in_planes, out_planes, kernel_size=(3, 1, 1),
                     stride=(t_stride, stride, stride),
                     padding=(1, 0, 0), bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, t_stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        # 1x3x3 conv
        self.conv1 = conv1x3x3(inplanes, planes, stride=stride, t_stride=t_stride)
        self.bn1 = nn.BatchNorm3d(planes)
        self.relu = nn.ReLU(inplace=True)
        # 1x3x3 conv
        self.conv2 = conv1x3x3(planes, planes)
        self.bn2 = nn.BatchNorm3d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out

class BasicBlockSTF_Plain(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, t_stride=1, downsample=None):
        super(BasicBlockSTF_Plain, self).__init__()
        # 1x3x3 conv
        self.conv1 = conv1x3x3(inplanes, planes, stride=stride, t_stride=t_stride)
        self.bn1 = nn.BatchNorm3d(planes)
        self.relu = nn.ReLU(inplace=True)
        # 3x1x1 conv
        self.conv1_2 = conv3x1x1(planes, planes)
        self.bn1_2 = nn.BatchNorm3d(planes)
        # 1x3x3 conv
        self.conv2 = conv1x3x3(planes, planes)
        self.bn2 = nn.BatchNorm3d(planes)
        # 3x1x1 conv
        self.conv2_2 = conv3x1x1(planes, planes)
        self.bn2_2 = nn.BatchNorm3d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv1_2(out)
        out = self.bn1_2(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out = self.relu(out)
        out = self.conv2_2(out)
        out = self.bn2_2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out

class BasicBlockSTF_Residual(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, t_stride=1, downsample=None):
        super(BasicBlockSTF_Residual, self).__init__()
        # 1x3x3 conv
        self.conv1 = conv1x3x3(inplanes, planes, stride=stride, t_stride=t_stride)
        self.bn1 = nn.BatchNorm3d(planes)
        self.relu = nn.ReLU(inplace=True)
        # 3x1x1 conv
        self.conv1_2 = conv3x1x1(planes, planes)
        self.bn1_2 = nn.BatchNorm3d(planes)
        # 1x3x3 conv
        self.conv2 = conv1x3x3(planes, planes)
        self.bn2 = nn.BatchNorm3d(planes)
        # 3x1x1 conv
        self.conv2_2 = conv3x1x1(planes, planes)
        self.bn2_2 = nn.BatchNorm3d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out_1 = self.conv1_2(out)
        out_1 = self.bn1_2(out_1)
        out_1 = self.relu(out_1)

        out_2 = out + out_1

        out_2 = self.conv2(out_2)
        out_2 = self.bn2(out_2)

        out_3 = self.relu(out_2)
        out_3 = self.conv2_2(out_3)
        out_3 = self.bn2_2(out_3)

        out_4 = out_2 + out_3

        if self.downsample is not None:
            residual = self.downsample(x)

        out_4 += residual
        out_4 = self.relu(out_4)

        return out_4

class Bottleneck3D_100(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, t_stride=1, downsample=None):
        super(Bottleneck3D_100, self).__init__()
        self.conv1 = nn.Conv3d(inplanes, planes, kernel_size=(3, 1, 1), 
                               stride=(t_stride, 1, 1),
                               padding=(1, 0, 0), bias=False)
        self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = nn.Conv3d(planes, planes, kernel_size=(1, 3, 3), 
                               stride=(1, stride, stride), padding=(0, 1, 1), bias=False)
        self.bn2 = nn.BatchNorm3d(planes)
        self.conv3 = nn.Conv3d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm3d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out

class Bottleneck3D_000(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, t_stride=1, downsample=None):
        super(Bottleneck3D_000, self).__init__()
        self.conv1 = nn.Conv3d(inplanes, planes, kernel_size=1, 
                               stride=[t_stride, 1, 1], bias=False)
        self.bn1 = nn.BatchNorm3d(planes)
        self.conv2 = nn.Conv3d(planes, planes, kernel_size=(1, 3, 3), 
                               stride=[1, stride, stride], padding=(0, 1, 1), bias=False)
        self.bn2 = nn.BatchNorm3d(planes)
        self.conv3 = nn.Conv3d(planes, planes * self.expansion, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm3d(planes * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class ResNet3D(nn.Module):

    def __init__(self, block, layers, num_classes=1000, feat=False, lite=False):
        if not isinstance(block, list):
            block = [block] * 4
        else:
            assert(len(block)) == 4, "Block number must be 4 for ResNet-Stype networks."
        self.inplanes = 64
        super(ResNet3D, self).__init__()
        self.feat = feat
        self.conv1 = nn.Conv3d(3, 64, kernel_size=(1, 7, 7), 
                               stride=(1, 2, 2), padding=(0, 3, 3),
                               bias=False)
        self.bn1 = nn.BatchNorm3d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1))
        self.layer1 = self._make_layer(block[0], 64, layers[0])
        self.layer2 = self._make_layer(block[1], 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block[2], 256, layers[2], stride=2, t_stride=2 if not lite else 1)
        self.layer4 = self._make_layer(block[3], 512, layers[3], stride=2, t_stride=2)
        self.avgpool = nn.AvgPool3d(kernel_size=(4, 7, 7), stride=1)
        self.feat_dim = 512 * block[0].expansion
        if not feat:
            self.fc = nn.Linear(512 * block[0].expansion, num_classes)

        for n, m in self.named_modules():
            if isinstance(m, nn.Conv3d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm3d):
                if block[0] is BasicBlockSTF_Residual and "_2" in n:
                    nn.init.constant_(m.weight, 0)
                else:
                    nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def _make_layer(self, block, planes, blocks, stride=1, t_stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv3d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=(t_stride, stride, stride), bias=False),
                nn.BatchNorm3d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride=stride, t_stride=t_stride, downsample=downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        if not self.feat:
            x = self.fc(x)

        return x


def part_state_dict(state_dict, model_dict):
    pretrained_dict = {k: v for k, v in state_dict.items() if k in model_dict}
    pretrained_dict = inflate_state_dict(pretrained_dict, model_dict)
    model_dict.update(pretrained_dict)
    return model_dict


def inflate_state_dict(pretrained_dict, model_dict):
    for k in pretrained_dict.keys():
        if pretrained_dict[k].size() != model_dict[k].size():
            assert(pretrained_dict[k].size()[:2] == model_dict[k].size()[:2]), \
                   "To inflate, channel number should match."
            assert(pretrained_dict[k].size()[-2:] == model_dict[k].size()[-2:]), \
                   "To inflate, spatial kernel size should match."
            print("Layer {} needs inflation.".format(k))
            shape = list(pretrained_dict[k].shape)
            shape.insert(2, 1)
            t_length = model_dict[k].shape[2]
            pretrained_dict[k] = pretrained_dict[k].reshape(shape)
            if t_length != 1:
                pretrained_dict[k] = pretrained_dict[k].expand_as(model_dict[k]) / t_length
            assert(pretrained_dict[k].size() == model_dict[k].size()), \
                   "After inflation, model shape should match."
    return pretrained_dict

def resnet18_2d(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D(BasicBlock, [2, 2, 2, 2], feat=feat, **kwargs)
    if pretrained:
        state_dict = model_zoo.load_url(model_urls['resnet18'])
        if feat:
            new_state_dict = part_state_dict(state_dict, model.state_dict())
            model.load_state_dict(new_state_dict)
    return model

def resnet18_3d_plain(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D(BasicBlockSTF_Plain, [2, 2, 2, 2], feat=feat, **kwargs)
    if pretrained:
        state_dict = model_zoo.load_url(model_urls['resnet18'])
        if feat:
            new_state_dict = part_state_dict(state_dict, model.state_dict())
            model.load_state_dict(new_state_dict)
    return model

def resnet18_3d_residual(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-18 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D(BasicBlockSTF_Plain, [2, 2, 2, 2], feat=feat, **kwargs)
    if pretrained:
        state_dict = model_zoo.load_url(model_urls['resnet18'])
        if feat:
            new_state_dict = part_state_dict(state_dict, model.state_dict())
            model.load_state_dict(new_state_dict)
    return model

def resnet34_3d(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-34 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D(BasicBlockSTF_Residual, [3, 4, 6, 3], feat=feat, **kwargs)
    if feat:
        state_dict = part_state_dict(model_zoo.load_url(model_urls['resnet34']), model.state_dict())
    if pretrained:
        model.load_state_dict(state_dict)
    return model


def resnet50_3d(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-50 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D([Bottleneck3D_000, Bottleneck3D_000, Bottleneck3D_100, Bottleneck3D_100], 
                     [3, 4, 6, 3], feat=feat, **kwargs)
    if pretrained:
        state_dict = model_zoo.load_url(model_urls['resnet50'])
        if feat:
            new_state_dict = part_state_dict(state_dict, model.state_dict())
            model.load_state_dict(new_state_dict)
    return model

def resnet50_3d_lite(pretrained=False, feat=False, **kwargs):
    """Constructs a ResNet-50 model.
    Args:
        pretrained (bool): If True, returns a model pre-trained on ImageNet
    """
    model = ResNet3D([Bottleneck3D_000, Bottleneck3D_000, Bottleneck3D_000, Bottleneck3D_100], 
                     [3, 4, 6, 3], feat=feat, lite=True, **kwargs)
    if pretrained:
        state_dict = model_zoo.load_url(model_urls['resnet50'])
        if feat:
            new_state_dict = part_state_dict(state_dict, model.state_dict())
            model.load_state_dict(new_state_dict)
    return model

# def resnet101(pretrained=False, feat=False, **kwargs):
#     """Constructs a ResNet-101 model.
#     Args:
#         pretrained (bool): If True, returns a model pre-trained on ImageNet
#     """
#     model = ResNet(Bottleneck, [3, 4, 23, 3], feat=feat, **kwargs)
#     if feat:
#         state_dict = part_state_dict(model_zoo.load_url(model_urls['resnet101']), model.state_dict())
#     if pretrained:
#         model.load_state_dict(state_dict)
#     return model


# def resnet152(pretrained=False, feat=False, **kwargs):
#     """Constructs a ResNet-152 model.
#     Args:
#         pretrained (bool): If True, returns a model pre-trained on ImageNet
#     """
#     model = ResNet(Bottleneck, [3, 8, 36, 3], feat=feat, **kwargs)
#     if feat:
#         state_dict = part_state_dict(model_zoo.load_url(model_urls['resnet152']), model.state_dict())
#     if pretrained:
#         model.load_state_dict(state_dict)
#     return model
