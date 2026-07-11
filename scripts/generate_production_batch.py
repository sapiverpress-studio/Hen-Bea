import json
from pathlib import Path

FAMILIES = [
    ("clap_pulse", "steady clapping pulse", "{lead_desc} and {follow_desc} clap a steady musical pulse together in a warm music classroom.", "{lead_name} {lead_pos} and {follow_name} {follow_pos} stand side by side on a simple classroom rug with both hands clearly apart at chest height ready to clap a steady musical pulse, elbows bent, hands fully visible and separated from their bodies, both have planted feet and calm cheerful closed-mouth expressions, {leader_marker} {follower_marker}", "Animate a simple steady four-beat clapping lesson. {lead_name} and {follow_name} each bring their hands together for four clear claps at an even tempo, with small controlled elbow movement only. Keep both bodies planted and upright. Preserve calm cheerful closed-mouth expressions."),
    ("drum_count", "hand drum beat and counting", "{lead_desc} taps a small hand drum with one beater while {follow_desc} counts the beat with one raised finger in a warm music classroom.", "{lead_name} {lead_pos} stands behind one small round hand drum on a simple wooden stand and holds one short drum beater clearly in {lead_possessive} right hand above the centre of the drum, {follow_name} {follow_pos} stands beside {lead_objective} with one clear index finger raised beside the chest as if counting the beat, both have planted feet and calm cheerful closed-mouth expressions, hands, beater and drum remain fully readable, {leader_marker} {follower_marker}", "Animate one simple steady four-beat lesson. {lead_name} moves only the right forearm and hand to tap the drum four times with one beater at an even tempo. {follow_name} keeps the body planted and counts with four small controlled pulses of the already-raised index finger. Keep heads mostly still and mouths closed."),
    ("maraca_shake", "maraca shake and listening", "{lead_desc} shakes one maraca in a steady rhythm while {follow_desc} watches and marks the beat in a warm music classroom.", "{lead_name} {lead_pos} holds one large simple maraca clearly in {lead_possessive} right hand just beside the body, ready to shake it in a small controlled motion, {follow_name} {follow_pos} stands beside {lead_objective} with one hand lifted slightly as if marking the beat while listening, both children have planted feet and calm cheerful closed-mouth expressions, the maraca remains large and easy to read, {leader_marker} {follower_marker}", "Animate a steady maraca lesson. {lead_name} makes four small controlled side-to-side shakes with the single maraca using the right hand only. {follow_name} stays planted and marks the beat with four tiny pulses of one hand. Keep expressions calm and cheerful, and keep the maraca stable and readable."),
    ("note_card", "note card pointing and response", "{lead_desc} points to a large music note card while {follow_desc} responds with a small counting gesture in a warm music classroom.", "{lead_name} {lead_pos} stands beside one large upright note card on a simple stand and points clearly toward the centre of the card with one index finger, {follow_name} {follow_pos} stands beside {lead_objective} with one hand lifted in a small responding gesture, both children keep planted feet and calm cheerful closed-mouth expressions, the card is large and readable with a simple bold music symbol, {leader_marker} {follower_marker}", "Animate a simple teaching moment. {lead_name} makes four small repeated pointing motions toward the large note card using one hand. {follow_name} responds with four tiny counting or acknowledging hand pulses. Keep both bodies planted and keep the note card perfectly stable."),
    ("piano_key", "single piano key press", "{lead_desc} presses one piano key repeatedly while {follow_desc} watches and listens in a warm music classroom.", "{lead_name} {lead_pos} stands beside a simple upright piano or keyboard and holds one hand just above one clearly visible key ready to press it, {follow_name} {follow_pos} stands beside {lead_objective} watching with one small listening gesture, both children have planted feet, calm cheerful closed-mouth expressions and clearly readable hands, {leader_marker} {follower_marker}", "Animate a steady listening lesson. {lead_name} presses the same piano key four times with one clear repeated finger movement while keeping the rest of the body still. {follow_name} remains planted and makes four tiny listening or counting pulses with one hand. Keep the piano stable."),
    ("rhythm_sticks", "rhythm sticks tapping", "{lead_desc} taps two rhythm sticks together while {follow_desc} follows the beat in a warm music classroom.", "{lead_name} {lead_pos} holds two large simple rhythm sticks clearly separated at chest height ready to tap them together, {follow_name} {follow_pos} stands beside {lead_objective} with one hand lifted slightly to follow the beat, both children have planted feet and calm cheerful closed-mouth expressions, the sticks are thick and easy to read, {leader_marker} {follower_marker}", "Animate a steady rhythm exercise. {lead_name} taps the two rhythm sticks together four times with small controlled arm movement. {follow_name} stays planted and marks the beat with four small hand pulses. Keep the sticks clear, stable and separated."),
    ("triangle", "triangle strike and listen", "{lead_desc} strikes a triangle gently while {follow_desc} listens and marks the beat in a warm music classroom.", "{lead_name} {lead_pos} holds one large simple triangle clearly in one hand and one short striker in the other ready to strike it, {follow_name} {follow_pos} stands beside {lead_objective} with one listening gesture and calm cheerful expression, both children have planted feet and clearly readable hands, the triangle is large and easy to read, {leader_marker} {follower_marker}", "Animate a simple listening lesson. {lead_name} strikes the triangle four times with small controlled hand movement while keeping the triangle shape stable. {follow_name} stays planted and marks the beat with four tiny listening pulses of one hand. Keep faces calm and mouths closed."),
    ("long_short", "long and short sounds cards", "{lead_desc} points between long and short sound cards while {follow_desc} responds with a small beat gesture in a warm music classroom.", "{lead_name} {lead_pos} stands beside two large teaching cards, one labelled long with a long line and one labelled short with two short marks, and points clearly between them, {follow_name} {follow_pos} stands beside {lead_objective} with one small responding gesture, both children keep planted feet and calm cheerful closed-mouth expressions, the cards are large and readable, {leader_marker} {follower_marker}", "Animate a simple concept lesson. {lead_name} points slowly to the long card, then to the short card, repeating the long-short pattern twice with small controlled arm movement. {follow_name} stays planted and responds with four tiny beat pulses. Keep the cards stable and readable."),
    ("high_low", "high and low pointing", "{lead_desc} points to high and low symbols while {follow_desc} responds with a small gesture in a warm music classroom.", "{lead_name} {lead_pos} stands beside a large teaching board showing one symbol high and one symbol low and holds one hand ready to point upward and downward, {follow_name} {follow_pos} stands beside {lead_objective} with one small responding gesture, both children keep planted feet and calm cheerful closed-mouth expressions, the board is large and readable, {leader_marker} {follower_marker}", "Animate a simple concept lesson. {lead_name} points up to the high symbol, then down to the low symbol, repeating the high-low pattern twice with small controlled arm movement. {follow_name} stays planted and responds with four tiny hand pulses. Keep the board stable and readable."),
    ("copy_beat", "copy the beat", "{lead_desc} leads a simple beat pattern while {follow_desc} copies it in a warm music classroom.", "{lead_name} {lead_pos} holds both hands ready to demonstrate one simple beat pattern at chest height, {follow_name} {follow_pos} mirrors the pose ready to copy, both children have planted feet and calm cheerful closed-mouth expressions with hands fully visible and separated from their bodies, {leader_marker} {follower_marker}", "Animate a copy-the-beat lesson. {lead_name} makes four small beat motions with the hands at chest height, and {follow_name} repeats each motion just after {lead_objective} with a small controlled delay. Keep bodies planted, expressions stable and movements simple."),
]

VARIANTS = [
    (1, "Hen", "frontal centred square composition", "behind them is a warm music lesson room with a teaching board and one low shelf with a few large books"),
    (2, "Bea", "frontal centred square composition", "behind them is a warm music lesson room with a teaching board and one low shelf with a few large books"),
    (3, "Hen", "slightly wider square composition with more floor space", "behind them is a warm music lesson room with an upright piano and a teaching board"),
    (4, "Bea", "slightly wider square composition with more floor space", "behind them is a warm music lesson room with an upright piano and a teaching board"),
    (5, "Hen", "centred square composition with a round rug clearly visible", "behind them is a warm music lesson room with a teaching board, a round rug and a low shelf"),
    (6, "Bea", "centred square composition with a round rug clearly visible", "behind them is a warm music lesson room with a teaching board, a round rug and a low shelf"),
    (7, "Hen", "frontal square composition slightly closer but still showing the full body", "behind them is a warm music lesson room with an upright piano, a teaching board and one low shelf"),
    (8, "Bea", "frontal square composition slightly closer but still showing the full body", "behind them is a warm music lesson room with an upright piano, a teaching board and one low shelf"),
    (9, "both", "frontal centred square composition", "behind them is a warm music lesson room with an upright piano, a teaching board and one low shelf with large percussion instruments"),
]

DESC = {
    "Hen": "Hen, a young boy with short brown hair, round glasses, a green jumper and dark shorts",
    "Bea": "Bea, a young girl with blonde hair, a large blue bow, an orange shirt and teal dungarees",
}
PRONOUNS = {"Hen": ("his", "him"), "Bea": ("her", "her")}


def build_scenes():
    scenes = []
    for key, title, caption_t, image_t, video_t in FAMILIES:
        for n, leader, camera, background in VARIANTS:
            if leader == "Hen":
                lead_name, follow_name = "Hen", "Bea"
                lead_pos, follow_pos = "stands on the left", "stands on the right"
            elif leader == "Bea":
                lead_name, follow_name = "Bea", "Hen"
                lead_pos, follow_pos = "stands on the left", "stands on the right"
            else:
                lead_name, follow_name = "Hen", "Bea"
                lead_pos, follow_pos = "stands slightly left of centre", "stands slightly right of centre"
            lead_possessive, lead_objective = PRONOUNS[lead_name]
            leader_marker = "Hen's exact round glasses remain clearly visible," if lead_name == "Hen" else "Bea's large blue bow is simple, fixed and symmetrical,"
            follower_marker = "Bea's large blue bow is simple, fixed and symmetrical." if follow_name == "Bea" else "Hen's exact round glasses remain clearly visible."
            image_body = image_t.format(lead_name=lead_name, follow_name=follow_name, lead_pos=lead_pos, follow_pos=follow_pos, lead_possessive=lead_possessive, lead_objective=lead_objective, leader_marker=leader_marker, follower_marker=follower_marker)
            image_prompt = (
                "HNBEA_HEN, HNBEA_BEA, HNBEA_HEN is a young boy with short brown hair and round glasses wearing a green jumper and dark shorts, "
                "HNBEA_BEA is a young girl with blonde hair and a large blue bow wearing an orange shirt and teal dungarees, "
                f"indoor music lesson room in the same warm Hen and Bea world, {image_body}, {background}, no teacher, no extra characters, no clutter, {camera}, show full bodies from head to shoes, children's book illustration, flat colour, clean outlines, soft warm palette, simple readable shapes, consistent character design, no realistic rendering, no generic clip-art look"
            )
            video_prompt = (
                "Hen is the boy with short brown hair, exact round glasses, a green jumper and dark shorts. "
                "Bea is the girl with blonde hair, an exact large symmetrical blue bow, an orange shirt and teal dungarees. "
                + video_t.format(lead_name=lead_name, follow_name=follow_name, lead_objective=lead_objective)
                + " Preserve Hen's exact face and glasses. Preserve Bea's exact face and bow shape. Preserve clothing, colours, proportions, hairstyles and flat children's-book illustration style. Keep the piano, board, shelf, rug and room stable. Locked camera. No zoom. No pan. No cropping. No walking. No talking. No mouth movement. No head turning. No large body movement. No body morphing. No extra limbs or fingers. No new objects or characters. No scene change."
            )
            scenes.append({"scene_id": f"prod_{key}_{n:02d}", "title": f"{title.capitalize()} variant {n}", "image_prompt": image_prompt, "video_prompt": video_prompt, "lora_strength": 0.9, "steps": 9, "width": 768, "height": 768, "seed": -1, "video_model": "v2.3", "duration": 6, "resolution": 768, "expand_prompt": False, "training_caption_draft": caption_t.format(lead_desc=DESC[lead_name], follow_desc=DESC[follow_name])})
    return scenes


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scenes = build_scenes()
    Path(args.output).write_text(json.dumps(scenes, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenes)} scenes to {args.output}")


if __name__ == "__main__":
    main()
