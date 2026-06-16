# ascii_cube_to_donut_particles.py
# Cubo -> partículas -> donut -> partículas -> cubo (Loop Perfeito Corrigido)
# Saída: ascii_cube_donut.gif
# Requer: pip install pillow

import math
from PIL import Image, ImageDraw, ImageFont

W, H = 160, 90
SCALE = 10
FRAMES = 150  # 150 frames com 40ms de duração dá uma animação lisa de 6 segundos
ASCII = " .,:-=+*#%@"
CAMERA = 18.0
PROJ = 110.0

def rot(x, y, z, a, b, c):
    ca, sa = math.cos(a), math.sin(a)
    cb, sb = math.cos(b), math.sin(b)
    cc, sc = math.cos(c), math.sin(c)

    y, z = y * ca - z * sa, y * sa + z * ca
    x, z = x * cb + z * sb, -x * sb + z * cb
    x, y = x * cc - y * sc, x * sc + y * cc
    return x, y, z

# --- Geração do Cubo (Exatos 3456 pontos) ---
cube = []
n = 24  # 24 * 24 pontos * 6 faces = 3456 partículas completas (sem cortes!)
s = 3.0
for i in range(n):
    for j in range(n):
        u = -s + 2 * s * i / (n - 1)
        v = -s + 2 * s * j / (n - 1)
        cube.extend([
            (u, v, s), (u, v, -s),
            (s, u, v), (-s, u, v),
            (u, s, v), (u, -s, v)
        ])

# --- Geração do Donut (Exatos 3456 pontos) ---
torus = []
for i in range(72):
    t = 2 * math.pi * i / 72
    for j in range(48):  # 72 * 48 = 3456 partículas
        p = 2 * math.pi * j / 48
        x = (3.0 + 1.2 * math.cos(p)) * math.cos(t)
        y = (3.0 + 1.2 * math.cos(p)) * math.sin(t)
        z = 1.2 * math.sin(p)
        torus.append((x, y, z))

try:
    font = ImageFont.truetype("cour.ttf", 14)
except:
    font = ImageFont.load_default()

frames = []

for frame in range(FRAMES):
    progress = frame / FRAMES
    
    # Onda suave para a transição: vai do Cubo(0) para o Donut(1) e volta para o Cubo(0)
    phase = (math.sin(progress * 2 * math.pi - math.pi / 2) + 1) / 2

    # Rotação sincronizada para fechar 360 graus exatamente no final do loop
    rot_a = progress * 2 * math.pi * 2  # 2 voltas no eixo X
    rot_b = progress * 2 * math.pi * 1  # 1 volta no eixo Y
    rot_c = progress * 2 * math.pi * 1  # 1 volta no eixo Z

    pts = []
    for c, d in zip(cube, torus):
        # Transição das partículas
        x = c[0] * (1 - phase) + d[0] * phase
        y = c[1] * (1 - phase) + d[1] * phase
        z = c[2] * (1 - phase) + d[2] * phase

        # Rotação no espaço
        x, y, z = rot(x, y, z, rot_a, rot_b, rot_c)
        pts.append((x, y, z))

    projected = []
    for x, y, z in pts:
        zz = z + CAMERA
        ooz = 1 / zz

        sx = x * PROJ * ooz
        sy = -y * PROJ * ooz
        projected.append((sx, sy, zz, ooz))

    screen = [" "] * (W * H)
    zbuf = [-999999] * (W * H)

    for sx, sy, zz, ooz in projected:
        # Centralização fixa na tela (remove "tremedeiras")
        px = int(sx + W / 2)
        py = int(sy + H / 2)

        if 0 <= px < W and 0 <= py < H:
            idx = px + py * W

            if ooz > zbuf[idx]:
                zbuf[idx] = ooz
                
                # Fórmula de sombreamento restaurada para o padrão do autor
                shade = int(max(0, min(len(ASCII) - 1, (1 - zz / (CAMERA + 5)) * (len(ASCII) - 1))))
                screen[idx] = ASCII[shade]

    txt = ""
    for y in range(H):
        txt += "".join(screen[y * W:(y + 1) * W]) + "\n"

    img = Image.new("RGB", (W * SCALE, H * SCALE), "black")
    d = ImageDraw.Draw(img)

    box = d.multiline_textbbox((0, 0), txt, font=font)
    tw = box[2] - box[0]
    th = box[3] - box[1]

    d.multiline_text(
        ((img.width - tw) // 2, (img.height - th) // 2),
        txt,
        fill="white",
        font=font,
    )

    frames.append(img)

frames[0].save(
    "ascii_cube_donut.gif",
    save_all=True,
    append_images=frames[1:],
    duration=40,
    loop=0
)

print("ascii_cube_donut.gif gerado com loop perfeito e modelo corrigido!")