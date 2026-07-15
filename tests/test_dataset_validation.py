import numpy as np

from beansight_vn.dataset_validation import validate_dataset, validate_frame


def frame(episode, frame_index, action):
    image = np.indices((8, 8)).sum(axis=0) % 2
    image = np.repeat(image[..., None], 3, axis=2)
    return {
        "observation.images.top": image,
        "observation.images.wrist": image,
        "action": np.asarray(action, dtype=float),
        "episode_index": episode,
        "frame_index": frame_index,
    }


class FakeDataset:
    features = {
        "observation.images.top": {},
        "observation.images.wrist": {},
        "action": {},
    }

    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


def test_valid_dataset_passes():
    items = [frame(0, index, [index + joint for joint in range(6)]) for index in range(3)]
    report = validate_dataset(FakeDataset(items), dataset_name="fake")
    assert report.passed
    assert report.action_std == [np.std([0, 1, 2])] * 6


def test_dead_joint_and_camera_order_fail():
    dataset = FakeDataset(
        [frame(0, index, [0, index, index, index, index, index]) for index in range(3)]
    )
    dataset.features = {
        "observation.images.wrist": {},
        "observation.images.top": {},
        "action": {},
    }
    report = validate_dataset(dataset, dataset_name="bad")
    assert not report.passed
    assert any("camera order" in error for error in report.errors)
    assert any("constant action" in error for error in report.errors)


def test_frame_rejects_nonfinite_actions_and_missing_camera():
    item = frame(0, 0, [0, 1, 2, 3, 4, np.nan])
    del item["observation.images.wrist"]
    errors = validate_frame(item)
    assert "missing camera frame observation.images.wrist" in errors
    assert "action contains NaN or Inf" in errors


def test_frame_rejects_dead_camera_image():
    item = frame(0, 0, range(6))
    item["observation.images.top"] = np.zeros((8, 8, 3))
    assert "constant camera frame observation.images.top" in validate_frame(item)
