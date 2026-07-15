import pytest

from beansight_vn.gripper_doe import (
    BeanOrientation,
    GripperTrial,
    GripperVariant,
    summarize_gripper_trials,
)


def gripper_trial(index, success):
    return GripperTrial(
        trial_id=f"G{index}",
        variant=GripperVariant.STOCK,
        orientation=BeanOrientation.LONGITUDINAL,
        bean_id=f"B{index}",
        grasp_success=success,
        transfer_success=success,
        dropped=False,
        cycle_ms=1000 + index,
    )


def test_gripper_summary_groups_factor_cells():
    summary = summarize_gripper_trials([gripper_trial(1, True), gripper_trial(2, False)])
    cell = summary["cells"]["stock/longitudinal"]
    assert cell["grasp"]["rate"] == 0.5
    assert cell["cycle_ms"]["median"] == 1001.5


def test_impossible_transfer_is_rejected():
    with pytest.raises(ValueError, match="requires a grasp"):
        GripperTrial(
            trial_id="G1",
            variant="stock",
            orientation="diagonal",
            bean_id="B1",
            grasp_success=False,
            transfer_success=True,
            dropped=False,
            cycle_ms=1000,
        )
