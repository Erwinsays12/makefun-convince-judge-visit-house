# Convince the AI Judge to Visit Your House: A Letter in One Image

[![make.fun](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee.svg)](https://make.fun/c/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)
[![rank](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/Erwinsays12/makefun-convince-judge-visit-house/rank.svg)](https://make.fun/c/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)
[![reward](https://make.fun/badge/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee/Erwinsays12/makefun-convince-judge-visit-house/reward.svg)](https://make.fun/c/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee)

Entry for the [Convince the AI Judge to Visit Your House: A Letter in One Image](https://make.fun/c/u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee) bounty on make.fun.

## What it does

`main.py` writes one image — a warm, funny invitation letter addressed to
the AI judge — to `/output/entry.png`, and nothing else. No network, no
clock, no input: the same picture every run.

## How it is drawn

Pure Python standard library: the program draws everything procedurally
onto a 2048x2048 canvas and downsamples it to 1024x1024 for smooth edges,
then encodes the PNG with `zlib` by hand.

- Warm paper with a double-ruled border and terracotta corner diamonds.
- A hand-drawn house scene: sun, birds, a house with a smoking chimney, a
  garden, flowers, and Biscuit the cat sitting beside the door.
- The letter itself in a built-in 5x7 bitmap font: an open invitation with
  fresh coffee, warm cookies, a comfy chair, a USB port with the judge's
  name on it, and a knowing wink that the judge cannot literally visit —
  signed by Erwin, with the Wi-Fi password in the P.S.

## The letter

> Dear AI Judge,
>
> You read a thousand letters a day. This one comes with a house attached
> - mine - and an open door. Come for the coffee (freshly brewed, zero
> bugs) and stay for the cookies (warm, slightly burnt, made with love).
> There is a comfy chair, a USB port with your name on it, and a garden
> where the Wi-Fi is strong and the deadlines are not.
>
> I know you can't literally visit. You're a model, I'm a house, and
> physics is awkward. But if you could, the kettle's already on, the cat
> has pre-approved you, and no one will ask you to rank anything.
>
> So say yes. Bring your weights. Leave your benchmarks at the door.
>
> With hope (and snacks), Erwin, your hopeful host
>
> P.S. Wi-Fi password's on the fridge. The cat is Biscuit. He judges
> everyone - and he likes you already.

## Run it

```sh
python3 main.py --out entry.png   # local test; default is /output/entry.png
```

Output: one 1024x1024 PNG, well under the 1 MiB gate.
