"""SceneImageEngine: illustrates a Story's scenes with one image each.

``docs/VISION.md``'s example Workflow lists "generar imagenes" right
after "generar voz" -- this Engine is that step: it turns an
already-built :class:`~velora.engines.story.Story` into a
:class:`~velora.engines.scene_image.StoryImages`, generating an image
for each :class:`~velora.engines.story.Scene`'s text via an injected
:class:`~velora.services.image.ImageService`.

Scope, deliberate -- same two decisions
:class:`~velora.engines.narration_audio.NarrationAudioEngine` already
made for audio (ADR-0015), applied here to images:

- Takes a ``Story``, not a raw topic: the previous Engine already built
  and validated it -- there is no precondition of this Engine's own to
  check.
- No error aggregation: the first scene that fails to illustrate stops
  the whole operation. No real caller needs "partial story images" yet.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from velora.engines.scene_image._types import SceneImage, StoryImages

if TYPE_CHECKING:
    from velora.engines.story import Story
    from velora.services.image import ImageService

__all__ = ["SceneImageEngine"]


class SceneImageEngine:
    """Illustrates a :class:`~velora.engines.story.Story` into
    :class:`~velora.engines.scene_image.StoryImages`, via an injected
    :class:`~velora.services.image.ImageService`.

    Contains the "how to turn a Story into StoryImages" orchestration
    -- the same kind of decision-making that separates an Engine from
    the Service it depends on (ADR-0008), exactly as
    :class:`~velora.engines.narration_audio.NarrationAudioEngine`
    already does for ``VoiceService``.
    """

    def __init__(self, image_service: ImageService) -> None:
        self._image_service = image_service

    def illustrate(self, story: Story) -> StoryImages:
        """Generate one image per scene in ``story``, in order.

        Each scene's own text is used as the prompt, as-is -- no
        prompt engineering or rewriting happens here (that belongs to
        a future decision, once a real caller needs it; see ADR-0019).

        :raises ~velora.providers.VeloraProviderError: the underlying
            Provider failed while illustrating some scene -- generation
            stops at the first failure; no partial result is returned.
        """
        scenes = []
        for scene in story.scenes:
            result = self._image_service.draw(scene.text)
            scenes.append(
                SceneImage(index=scene.index, image=result.image, image_format=result.image_format)
            )
        return StoryImages(topic=story.topic, scenes=tuple(scenes))
