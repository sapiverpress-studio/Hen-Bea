import json
from pathlib import Path

CHARACTERS = (
    "HNBEA_HEN, HNBEA_BEA, HNBEA_HEN is a young boy with short brown hair and exact round glasses wearing a green jumper and dark shorts, "
    "HNBEA_BEA is a young girl with blonde hair and a large fixed symmetrical blue bow wearing an orange shirt and teal dungarees"
)
STYLE = (
    "children's book illustration, flat colour, clean outlines, soft warm palette, simple readable shapes, consistent character design, "
    "animation-ready, no realistic rendering, no generic clip-art look"
)
VIDEO_LOCK = (
    "Preserve Hen's exact face and round glasses. Preserve Bea's exact face and large blue bow. Preserve clothing, colours, proportions, hairstyles and flat children's-book style. "
    "Keep all furniture, teaching materials and room objects stable. Locked camera. No zoom, pan, crop, walking, talking, mouth movement, scene change, body morphing, extra limbs, extra fingers, new objects or new characters."
)

ACTIONS = [
    {
        "key": "clap_pulse",
        "title": "Clap a steady pulse",
        "prop": "no handheld props",
        "image": "{lead} holds both hands clearly apart at chest height ready to clap, while {follow} mirrors the pose ready to join in",
        "video": "Animate four controlled claps at an even tempo. {lead} claps first and {follow} joins half a beat later. Use small elbow and shoulder movement only.",
        "caption": "{lead_desc} leads four steady claps while {follow_desc} joins the pulse."
    },
    {
        "key": "drum_count",
        "title": "Play a hand drum and count",
        "prop": "one small round hand drum on a stable stand and one short beater",
        "image": "{lead} holds one short beater above the centre of a small hand drum, while {follow} raises one index finger to count",
        "video": "Animate four even drum taps using one beater. {follow} marks the four beats with small index-finger pulses.",
        "caption": "{lead_desc} taps a small hand drum four times while {follow_desc} counts the beat."
    },
    {
        "key": "maraca",
        "title": "Shake a maraca and listen",
        "prop": "one large simple maraca",
        "image": "{lead} holds one large maraca clearly in the right hand, while {follow} makes a small listening gesture",
        "video": "Animate four small side-to-side maraca shakes with the right hand. {follow} marks the beat with tiny controlled hand pulses.",
        "caption": "{lead_desc} shakes one maraca in a steady rhythm while {follow_desc} listens and marks the beat."
    },
    {
        "key": "note_card",
        "title": "Point to a music note card",
        "prop": "one large upright card showing a bold single music note",
        "image": "{lead} points clearly to a large upright music-note card, while {follow} responds with one raised hand",
        "video": "Animate four small pointing motions toward the note card. {follow} responds with four tiny acknowledging hand pulses.",
        "caption": "{lead_desc} points to a large music-note card while {follow_desc} responds."
    },
    {
        "key": "piano_key",
        "title": "Press one piano key",
        "prop": "one simple upright piano with a clearly visible keyboard",
        "image": "{lead} holds one finger above a single visible piano key, while {follow} watches with a small listening gesture",
        "video": "Animate four presses of the same piano key with one finger. {follow} stays still except for four tiny listening pulses.",
        "caption": "{lead_desc} presses one piano key four times while {follow_desc} watches and listens."
    },
    {
        "key": "rhythm_sticks",
        "title": "Tap rhythm sticks",
        "prop": "two thick clearly separated rhythm sticks",
        "image": "{lead} holds two thick rhythm sticks apart at chest height, while {follow} holds one hand ready to mark the beat",
        "video": "Animate four controlled taps of the two rhythm sticks. {follow} marks the beat with four small hand pulses.",
        "caption": "{lead_desc} taps two rhythm sticks together while {follow_desc} follows the beat."
    },
    {
        "key": "triangle",
        "title": "Strike a triangle and listen",
        "prop": "one large triangle and one short striker",
        "image": "{lead} holds one large triangle in one hand and one short striker in the other, while {follow} makes a listening gesture",
        "video": "Animate four gentle triangle strikes with small hand movement. {follow} marks the beat with four tiny listening pulses.",
        "caption": "{lead_desc} strikes a triangle gently while {follow_desc} listens."
    },
    {
        "key": "long_short",
        "title": "Compare long and short sounds",
        "prop": "two large teaching cards, one with a long line and one with two short marks",
        "image": "{lead} points between a long-sound card and a short-sound card, while {follow} prepares to answer",
        "video": "Animate {lead} pointing to the long card and then the short card twice. {follow} answers with four small hand pulses.",
        "caption": "{lead_desc} compares long and short sound cards while {follow_desc} responds."
    },
    {
        "key": "high_low",
        "title": "Show high and low sounds",
        "prop": "one large board showing a high symbol and a low symbol",
        "image": "{lead} holds one hand ready to point up and down beside a high-and-low teaching board, while {follow} prepares to respond",
        "video": "Animate {lead} pointing high, then low, repeating the pattern twice. {follow} responds with four small controlled hand pulses.",
        "caption": "{lead_desc} points to high and low symbols while {follow_desc} responds."
    },
    {
        "key": "copy_beat",
        "title": "Copy a beat pattern",
        "prop": "no handheld props",
        "image": "{lead} holds both hands ready to demonstrate a simple beat pattern, while {follow} watches in a matching ready pose",
        "video": "Animate four small beat motions from {lead}. {follow} copies each motion after a short clear delay.",
        "caption": "{lead_desc} demonstrates a simple beat pattern while {follow_desc} copies it."
    },
]

LAYOUTS = [
    {
        "name": "rug_seated",
        "lead": "Hen", "follow": "Bea",
        "pose": "Hen and Bea sit cross-legged on a round classroom rug, Hen slightly left and Bea slightly right, both upright with full hands visible",
        "zone": "centre rug area with a low shelf and a few large books behind them",
        "camera": "wide frontal square shot showing both seated bodies and generous floor space"
    },
    {
        "name": "board_standing",
        "lead": "Bea", "follow": "Hen",
        "pose": "Bea stands beside the teaching board on the left while Hen stands farther right, both in balanced three-quarter poses",
        "zone": "teaching-board wall with large simple lesson symbols and no other clutter",
        "camera": "board-focused medium-wide square shot showing full bodies"
    },
    {
        "name": "piano_seated",
        "lead": "Hen", "follow": "Bea",
        "pose": "Hen sits on a simple piano stool at the keyboard while Bea stands beside the piano, turned slightly toward him",
        "zone": "piano corner with one upright piano and a small framed music picture",
        "camera": "piano-focused side three-quarter square shot showing both children from head to shoes"
    },
    {
        "name": "percussion_corner",
        "lead": "Bea", "follow": "Hen",
        "pose": "Bea stands near the percussion shelf while Hen sits on a low stool beside her, both facing slightly toward each other",
        "zone": "percussion corner with one low shelf holding only two large instruments",
        "camera": "medium-wide diagonal square shot with clear separation between both children"
    },
    {
        "name": "floor_cards",
        "lead": "Hen", "follow": "Bea",
        "pose": "Hen kneels on one knee beside large floor cards while Bea sits cross-legged opposite him, both hands clearly visible",
        "zone": "open floor-card area beside a low table and one basket",
        "camera": "slightly elevated wide square shot centred on the floor activity"
    },
    {
        "name": "window_stools",
        "lead": "Bea", "follow": "Hen",
        "pose": "Bea sits on a low stool near the window while Hen stands beside her, both angled inward toward the lesson material",
        "zone": "bright window corner with simple curtains and one small plant on a high shelf",
        "camera": "medium full-body square shot with visible window light and uncluttered floor"
    },
    {
        "name": "table_activity",
        "lead": "Hen", "follow": "Bea",
        "pose": "Hen and Bea sit on opposite sides of a low rectangular activity table, both turned enough for their faces and hands to remain visible",
        "zone": "low-table learning area with one plain storage unit behind them",
        "camera": "wide three-quarter square shot showing the table, both seated children and their hands"
    },
    {
        "name": "rug_one_kneeling",
        "lead": "Bea", "follow": "Hen",
        "pose": "Bea kneels upright on the rug while Hen stands beside her, both facing the lesson prop at the centre",
        "zone": "centre rug area with the piano visible far in the background and clear empty floor around them",
        "camera": "low medium-wide square shot creating a visibly different height relationship"
    },
    {
        "name": "close_teaching_pair",
        "lead": "Hen", "follow": "Bea",
        "pose": "Hen stands closer to the teaching material in the foreground while Bea stands one step behind and to the side, both full bodies visible",
        "zone": "simple lesson display area with one freestanding easel and a distant shelf",
        "camera": "closer full-body square shot with layered foreground and background positions"
    },
]

DESC = {
    "Hen": "Hen, the boy with short brown hair, round glasses, a green jumper and dark shorts",
    "Bea": "Bea, the girl with blonde hair, a large blue bow, an orange shirt and teal dungarees",
}


def build_scenes():
    scenes = []
    for action in ACTIONS:
        for variant_number, layout in enumerate(LAYOUTS, start=1):
            lead = layout["lead"]
            follow = layout["follow"]
            action_image = action["image"].format(lead=lead, follow=follow)
            image_prompt = (
                f"{CHARACTERS}, indoor music lesson room in the same warm Hen and Bea world, "
                f"{layout['pose']}, {action_image}, {action['prop']}, {layout['zone']}, "
                f"{layout['camera']}, calm cheerful closed-mouth expressions, no teacher, no extra characters, no clutter, "
                f"all hands and props fully separated and easy to read, {STYLE}"
            )
            video_prompt = (
                f"Hen is the boy with short brown hair, exact round glasses, a green jumper and dark shorts. "
                f"Bea is the girl with blonde hair, an exact large symmetrical blue bow, an orange shirt and teal dungarees. "
                f"Keep the starting posture: {layout['pose']}. "
                + action["video"].format(lead=lead, follow=follow)
                + " Use restrained, readable movement appropriate to the seated, kneeling or standing pose. "
                + VIDEO_LOCK
            )
            scenes.append({
                "scene_id": f"prod_{action['key']}_{variant_number:02d}",
                "title": f"{action['title']} — {layout['name'].replace('_', ' ')}",
                "variation": {
                    "room_zone": layout["zone"],
                    "posture": layout["pose"],
                    "framing": layout["camera"],
                    "interaction": f"{lead} leads; {follow} responds",
                    "action_family": action["key"],
                },
                "image_prompt": image_prompt,
                "video_prompt": video_prompt,
                "lora_strength": 0.9,
                "steps": 9,
                "width": 768,
                "height": 768,
                "seed": -1,
                "video_model": "v2.3",
                "duration": 6,
                "resolution": 768,
                "expand_prompt": False,
                "training_caption_draft": action["caption"].format(
                    lead_desc=DESC[lead], follow_desc=DESC[follow]
                ),
            })
    return scenes


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scenes = build_scenes()
    Path(args.output).write_text(json.dumps(scenes, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenes)} varied scenes to {args.output}")


if __name__ == "__main__":
    main()
