import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import lightning.pytorch as pl
from pytorch_lightning.loggers import WandbLogger
from torchmetrics.classification import Accuracy, Precision, Recall


class Classifer(nn.Module):
    def __init__(self):
        super(Classifer, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(28 * 28, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 10),
        )

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.layers(x)


class LitClassifer(pl.LightningModule):
    def __init__(self, lr=1e-4, batch_size=64):
        super(LitClassifer, self).__init__()
        self.model = Classifer()
        self.lr = lr
        self.batch_size = batch_size

        self.criterion = F.cross_entropy

        self.accuracy = Accuracy(task="multiclass", num_classes=10)
        self.precision = Precision(task="multiclass", num_classes=10)
        self.recall = Recall(task="multiclass", num_classes=10)

        self.save_hyperparameters()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch

        y_hat = self(x)

        loss = self.criterion(y_hat, y)
        acc = self.accuracy(y_hat, y)
        prec = self.precision(y_hat, y)
        rec = self.recall(y_hat, y)

        self.log("train_loss", loss, on_step=True, prog_bar=True)
        self.log("train_acc", acc, on_step=True)
        self.log("train_prec", prec, on_step=True)
        self.log("train_rec", rec, on_step=True)

        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch

        y_hat = self(x)

        loss = self.criterion(y_hat, y)
        acc = self.accuracy(y_hat, y)
        prec = self.precision(y_hat, y)
        rec = self.recall(y_hat, y)

        self.log("val_loss", loss)
        self.log("val_acc", acc)
        self.log("val_prec", prec)
        self.log("val_rec", rec)

        return loss

    def configure_optimizers(self):
        return torch.optim.SGD(self.parameters(), lr=self.lr, momentum=0.9)

    def prepare_data(self):
        torchvision.datasets.QMNIST(root="qmnist/data", what="train", download=True)
        torchvision.datasets.QMNIST(root="qmnist/data", what="test", download=True)

    def train_dataloader(self):
        return torch.utils.data.DataLoader(
            torchvision.datasets.QMNIST(
                root="qmnist/data",
                what="train",
                transform=torchvision.transforms.ToTensor(),
            ),
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=4,
            persistent_workers=True,
        )

    def val_dataloader(self):
        return torch.utils.data.DataLoader(
            torchvision.datasets.QMNIST(
                root="qmnist/data",
                what="test",
                transform=torchvision.transforms.ToTensor(),
            ),
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=2,
            persistent_workers=True,
        )


if __name__ == "__main__":
    model = LitClassifer()
    logger = WandbLogger(
        project="qmnist", save_dir="qmnist/logs", log_model=True, save_code=True
    )
    logger.watch(model, log="all")
    trainer = pl.Trainer(
        logger=logger,
        max_epochs=20,
        default_root_dir="qmnist/logs",
        val_check_interval=0.5,
    )
    trainer.fit(model)
