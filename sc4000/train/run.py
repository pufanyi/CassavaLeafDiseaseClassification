from datasets import load_dataset, Dataset
from typing import Tuple
from datetime import datetime

import argparse
import wandb
import os

from sc4000.train.models import load_model, Model
from sc4000.utils.label_utils import label_mapping
from sc4000.utils.format import format_args
from sc4000.utils.logger import enable_debug_mode, setup_logger


logger = setup_logger(__name__)


def setup_args():
    parser = argparse.ArgumentParser(description="Train a model on a dataset")
    parser.add_argument("--model", type=str, help="Name of the model to train")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Name of the dataset to use",
        default="pufanyi/cassava-leaf-disease-classification",
    )
    parser.add_argument(
        "--subset",
        type=str,
        help="Subset of the dataset to use",
        default="default",
    )
    parser.add_argument(
        "--model_args", type=str, help="Arguments for the model", default="{}"
    )
    parser.add_argument(
        "--training_args",
        type=str,
        help="Arguments for training the model",
        default="{}",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory to save the model to",
        default="output/models",
    )
    parser.add_argument(
        "--wandb_project",
        type=str,
        help="Weights and Biases project to log to",
        default="sc4000",
    )
    parser.add_argument(
        "--wandb_run_name",
        type=str,
        help="Name of the Weights and Biases run",
        default="default",
    )
    parser.add_argument("--seed", type=int, help="Seed for reproducibility", default=28)
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--disable_wandb", action="store_true", help="Disable Weights and Biases"
    )
    return parser.parse_args()


def setup_wandb(args):
    if not args.disable_wandb:
        wandb.init(
            project=args.wandb_project,
            name=args.wandb_run_name,
        )
        logger.info("Weights and Biases initialized")
    else:
        logger.info("Weights and Biases disabled")


def get_dataset(
    dataset_name: str, subset: str, seed: int = 42
) -> Tuple[Dataset, Dataset]:
    data = load_dataset(dataset_name, subset)
    train_ds, val_ds = data["train"], data["validation"]
    train_ds = train_ds.shuffle(seed=seed)
    return train_ds, val_ds


if __name__ == "__main__":
    args = setup_args()

    if args.debug:
        enable_debug_mode()
        logger = setup_logger(__name__)

    setup_wandb(args)

    logger.info(f"Training model {args.model} on dataset {args.dataset}")
    train_ds, val_ds = get_dataset(args.dataset, args.subset, args.seed)
    id2label, label2id = label_mapping(train_ds)

    model_args = format_args(args.model_args)

    model: Model = load_model(
        args.model, id2label=id2label, label2id=label2id, **model_args
    )

    logger.info(f"Loaded model {model.name}")

    now_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_folder = os.path.join(args.output_dir, f"{model.name}_{now_time}")

    training_args = format_args(args.training_args)
    model.train(train_ds, val_ds, output_dir=output_folder, **training_args)

    logger.info(f"Training complete, model saved to {output_folder}")
