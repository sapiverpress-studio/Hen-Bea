import os
import random

import gradio as gr
import spaces
import torch
from diffusers import ZImagePipeline
from huggingface_hub import HfApi

APP_VERSION = "HB-GITHUB-SOURCE-2026-07-10-1"
BASE_MODEL = "Tongyi-MAI/Z-Image-Turbo"
LORA_REPO = "sapiverpress/hen-bea-lora"
HF_TOKEN = os.getenv("HF_TOKEN")

DEFAULT_PROMPT = """HNBEA_HEN, HNBEA_BEA,
HNBEA_HEN is a young boy with short brown hair and round glasses wearing a green jumper,
HNBEA_BEA is a young girl with blonde hair and a blue bow wearing orange-and-teal dungarees,
Hen and Bea standing together on a warm garden path outside the Music House,
Hen slightly off balance as though he is about to stumble,
Bea clapping a steady beat and smiling encouragingly,
children's book illustration, flat colour"""

pipe = None
lora_file = None


def find_lora_file():
    api = HfApi(token=HF_TOKEN)
    files = api.list_repo_files(
        repo_id=LORA_REPO,
        repo_type="model",
        token=HF_TOKEN,
    )
    candidates = [name for name in files if name.lower().endswith(".safetensors")]
    if not candidates:
        raise FileNotFoundError(f"No .safetensors file found in {LORA_REPO}")
    preferred = [name for name in candidates if "hen" in name.lower() and "bea" in name.lower()]
    return preferred[0] if preferred else candidates[0]


@spaces.GPU(duration=120)
def generate(prompt, strength, width, height, steps, seed):
    global pipe, lora_file

    if not HF_TOKEN:
        raise gr.Error("HF_TOKEN secret is missing")

    prompt = (prompt or "").strip()
    if not prompt:
        raise gr.Error("Enter a prompt")

    if seed is None or int(seed) < 0:
        seed = random.randint(0, 2147483647)
    seed = int(seed)

    if lora_file is None:
        lora_file = find_lora_file()

    if pipe is None:
        pipe = ZImagePipeline.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.bfloat16,
            token=HF_TOKEN,
        )
        pipe.load_lora_weights(
            LORA_REPO,
            weight_name=lora_file,
            token=HF_TOKEN,
            adapter_name="hen_bea",
        )
        pipe.to("cuda")

    pipe.set_adapters(["hen_bea"], adapter_weights=[float(strength)])
    generator = torch.Generator(device="cuda").manual_seed(seed)

    image = pipe(
        prompt=prompt,
        width=int(width),
        height=int(height),
        num_inference_steps=int(steps),
        guidance_scale=0.0,
        generator=generator,
    ).images[0]

    return image, seed, f"Loaded LoRA: {lora_file}"


with gr.Blocks(title="Hen & Bea Generator") as demo:
    gr.Markdown(f"# Hen & Bea Generator\n\nApp version: `{APP_VERSION}`")
    prompt = gr.Textbox(label="Prompt", value=DEFAULT_PROMPT, lines=10)
    run = gr.Button("GENERATE IMAGE", variant="primary")

    with gr.Accordion("Settings", open=False):
        strength = gr.Slider(0.1, 1.5, value=0.9, step=0.05, label="LoRA strength")
        steps = gr.Slider(4, 20, value=9, step=1, label="Inference steps")
        width = gr.Radio([768, 896, 1024], value=768, label="Width")
        height = gr.Radio([768, 896, 1024], value=768, label="Height")
        seed = gr.Number(value=-1, precision=0, label="Seed (-1 = random)")

    output = gr.Image(label="Generated image", type="pil")
    used_seed = gr.Number(label="Used seed", precision=0)
    status = gr.Textbox(label="Status", interactive=False)

    run.click(
        fn=generate,
        inputs=[prompt, strength, width, height, steps, seed],
        outputs=[output, used_seed, status],
    )


demo.queue().launch()
