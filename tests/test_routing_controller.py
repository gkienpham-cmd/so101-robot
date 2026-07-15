from beansight_vn.controller import BeanSightController
from beansight_vn.models import Decision, Label, PerceptionResult
from beansight_vn.routing import route_perception


class FixedClassifier:
    def __init__(self, result):
        self.result = result
        self.seen_frame = None

    def classify(self, frame, **_metadata):
        self.seen_frame = frame
        return self.result


def test_fail_still_routing():
    assert route_perception(PerceptionResult(Label.VISIBLE_REJECT, 0.79), 0.8) is Decision.NO_MOTION
    assert route_perception(PerceptionResult(Label.ACCEPTABLE, 1.0), 0.8) is Decision.NO_MOTION
    assert route_perception(PerceptionResult(Label.VISIBLE_REJECT, 0.8), 0.8) is Decision.REJECT


def test_controller_uses_shared_frame_but_stays_unarmed():
    frame = object()
    classifier = FixedClassifier(PerceptionResult(Label.VISIBLE_REJECT, 0.95))
    controller = BeanSightController(classifier)
    outcome = controller.handle_observation({"observation.images.top": frame})
    assert classifier.seen_frame is frame
    assert outcome.decision is Decision.REJECT
    assert not outcome.motion_executed


def test_armed_controller_executes_exactly_one_callback():
    calls = []
    classifier = FixedClassifier(PerceptionResult(Label.VISIBLE_REJECT, 0.95))
    controller = BeanSightController(
        classifier,
        armed=True,
        execute_reject=lambda observation: calls.append(observation) or "done",
    )
    observation = {"observation.images.top": "frame"}
    outcome = controller.handle_observation(observation)
    assert calls == [observation]
    assert outcome.motion_executed
    assert outcome.callback_result == "done"
