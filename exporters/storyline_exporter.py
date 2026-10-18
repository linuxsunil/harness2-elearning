"""
Storyline XML Exporter
Converts a scenario JSON dict to an Articulate Storyline 360 compatible XML
structure. Import via File > Import > XML in Storyline 360.

The XML follows Storyline's slide/layer/trigger schema so it can be
imported as a story fragment and wired into an existing project.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


def _slide_id(n: int) -> str:
    return f"slide_{n:03d}"


def _layer_id(slide: int, layer: int) -> str:
    return f"slide_{slide:03d}_layer_{layer:02d}"


def export(scenario: dict, domain: str = "", agent_label: str = "Domain-Adapted") -> str:
    """
    Returns Storyline-compatible XML as a string.
    """
    title = scenario.get("title", "Branching Scenario")
    context = scenario.get("context", "")
    scenes = scenario.get("scenes", [])
    tags = scenario.get("tags", [])

    root = ET.Element("story")
    root.set("title", title)
    root.set("domain", domain)
    root.set("agent", agent_label)
    root.set("generated", datetime.now().isoformat())
    root.set("source", "harness2-elearning")

    # Metadata
    meta = ET.SubElement(root, "metadata")
    ET.SubElement(meta, "title").text = title
    ET.SubElement(meta, "context").text = context
    ET.SubElement(meta, "domain").text = domain
    tags_el = ET.SubElement(meta, "tags")
    for t in tags:
        ET.SubElement(tags_el, "tag").text = t

    # Slides section
    slides_el = ET.SubElement(root, "slides")

    # Slide 0 — Title / Context slide
    title_slide = ET.SubElement(slides_el, "slide")
    title_slide.set("id", _slide_id(0))
    title_slide.set("type", "intro")
    title_slide.set("title", "Introduction")
    title_layer = ET.SubElement(title_slide, "layer")
    title_layer.set("id", _layer_id(0, 0))
    title_layer.set("name", "Base Layer")
    _add_text_object(title_layer, "txt_title", title, role="heading")
    _add_text_object(title_layer, "txt_context", context, role="body")
    _add_button(title_layer, "btn_start", "Begin Scenario",
                trigger_type="jump", target=_slide_id(1))

    # One slide per scene
    for i, scene in enumerate(scenes):
        slide_num = i + 1
        situation = scene.get("situation", "")
        choices = scene.get("choices", [])

        # Determine next target
        if slide_num < len(scenes):
            next_target = _slide_id(slide_num + 1)
        else:
            next_target = _slide_id(slide_num + 1)  # summary slide

        slide = ET.SubElement(slides_el, "slide")
        slide.set("id", _slide_id(slide_num))
        slide.set("type", "decision")
        slide.set("title", f"Scene {slide_num}")
        slide.set("scene_index", str(i))

        # Base layer — situation + choice buttons
        base = ET.SubElement(slide, "layer")
        base.set("id", _layer_id(slide_num, 0))
        base.set("name", "Base Layer")

        _add_text_object(base, f"txt_slide_{slide_num}_label",
                         f"Scene {slide_num} of {len(scenes)}", role="label")
        _add_text_object(base, f"txt_slide_{slide_num}_situation",
                         situation, role="body")

        for j, choice in enumerate(choices):
            key = choice.get("key", str(j + 1))
            text = choice.get("text", "")
            correct = choice.get("correct", False)
            feedback = choice.get("feedback", "")
            layer_id = _layer_id(slide_num, j + 1)
            btn_id = f"btn_slide_{slide_num}_choice_{key}"

            # Button on base layer → shows feedback layer
            _add_button(base, btn_id,
                        f"{key}. {text}",
                        trigger_type="show_layer",
                        target=layer_id,
                        data={"correct": str(correct).lower(), "choice_key": key})

            # Feedback layer
            fb_layer = ET.SubElement(slide, "layer")
            fb_layer.set("id", layer_id)
            fb_layer.set("name", f"Feedback {key}")
            fb_layer.set("correct", str(correct).lower())

            verdict = "Correct!" if correct else "Not quite."
            fb_icon = "✓" if correct else "✗"
            _add_text_object(fb_layer, f"txt_fb_{slide_num}_{key}_verdict",
                             f"{fb_icon} {verdict}", role="verdict")
            _add_text_object(fb_layer, f"txt_fb_{slide_num}_{key}_body",
                             feedback, role="feedback")

            # Continue button
            _add_button(fb_layer, f"btn_fb_{slide_num}_{key}_continue",
                        "Continue →",
                        trigger_type="hide_layer_jump",
                        target=next_target,
                        data={"from_layer": layer_id, "correct": str(correct).lower()})

            # Variables: increment score if correct
            if correct:
                var_el = ET.SubElement(fb_layer, "variable_action")
                var_el.set("variable", "score")
                var_el.set("action", "add")
                var_el.set("value", "1")
                var_el.set("trigger", f"btn_fb_{slide_num}_{key}_continue_click")

    # Summary / Results slide
    summary_slide_num = len(scenes) + 1
    summary = ET.SubElement(slides_el, "slide")
    summary.set("id", _slide_id(summary_slide_num))
    summary.set("type", "results")
    summary.set("title", "Results")
    s_layer = ET.SubElement(summary, "layer")
    s_layer.set("id", _layer_id(summary_slide_num, 0))
    s_layer.set("name", "Base Layer")
    _add_text_object(s_layer, "txt_summary_heading",
                     "Scenario Complete", role="heading")
    _add_text_object(s_layer, "txt_summary_score",
                     "%score% / %total% correct", role="score_display")
    _add_button(s_layer, "btn_restart", "↩ Try Again",
                trigger_type="jump", target=_slide_id(1))

    # Variables declaration
    vars_el = ET.SubElement(root, "variables")
    _add_var(vars_el, "score", "number", "0")
    _add_var(vars_el, "total", "number", str(len(scenes)))

    # Triggers summary (human-readable reference)
    triggers_doc = ET.SubElement(root, "triggers_reference")
    triggers_doc.text = (
        "Each choice button shows its corresponding feedback layer. "
        "The Continue button in correct feedback layers increments 'score' by 1 "
        "and jumps to the next slide. Incorrect Continue buttons jump without scoring. "
        "Results slide displays %score% and %total% variables."
    )

    return _pretty_xml(root)


def _add_text_object(parent, obj_id, text, role="body"):
    el = ET.SubElement(parent, "object")
    el.set("id", obj_id)
    el.set("type", "text")
    el.set("role", role)
    el.text = text


def _add_button(parent, btn_id, label, trigger_type, target, data=None):
    el = ET.SubElement(parent, "object")
    el.set("id", btn_id)
    el.set("type", "button")
    el.set("label", label)
    trigger = ET.SubElement(el, "trigger")
    trigger.set("type", trigger_type)
    trigger.set("target", target)
    trigger.set("event", "click")
    if data:
        for k, v in data.items():
            trigger.set(k, v)


def _add_var(parent, name, var_type, default):
    el = ET.SubElement(parent, "variable")
    el.set("name", name)
    el.set("type", var_type)
    el.set("default", default)


def _pretty_xml(root) -> str:
    raw = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent="  ", encoding=None)


def export_to_file(scenario: dict, path: str, domain: str = "", agent_label: str = "Domain-Adapted"):
    with open(path, "w", encoding="utf-8") as f:
        f.write(export(scenario, domain=domain, agent_label=agent_label))
