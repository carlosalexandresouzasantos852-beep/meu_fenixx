import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput

print("🔥 SISTEMA DE FARM CARREGADO 🔥")

# ================= CONFIG =================
CARGO_IGNORADO = "00"
CARGO_MEMBRO = "Membro"
LIMITE_ADV = 5

PASTA_DADOS = "meu_bot_farm/data"
HISTORICO_FILE = f"{PASTA_DADOS}/historico_farm.json"
ADV_FILE = f"{PASTA_DADOS}/advs.json"
SEMANA_FILE = f"{PASTA_DADOS}/semanas.json"
CONFIG_FILE = f"{PASTA_DADOS}/config.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452153715912867901/VID-20251221-WA0034.mp4"

# ================= UTIL =================
def carregar_json(path, default):
    os.makedirs(PASTA_DADOS, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def semana_atual():
    return datetime.now().strftime("%Y-%W")

# ================= ADV =================
def add_adv(user_id):
    advs = carregar_json(ADV_FILE, {})
    advs[str(user_id)] = advs.get(str(user_id), 0) + 1
    salvar_json(ADV_FILE, advs)
    return advs[str(user_id)]

def remove_adv(user_id, qtd):
    advs = carregar_json(ADV_FILE, {})
    advs[str(user_id)] = max(advs.get(str(user_id), 0) - qtd, 0)
    salvar_json(ADV_FILE, advs)

def get_adv(user_id):
    advs = carregar_json(ADV_FILE, {})
    return advs.get(str(user_id), 0)

# ================= VIEW =================
class EntregaView(View):
    def __init__(self, member, meta, quantidade, primeira_farm):
        super().__init__(timeout=None)
        self.member = member
        self.meta = meta
        self.quantidade = quantidade
        self.primeira_farm = primeira_farm

    @discord.ui.button(label="✅ AUTORIZAR ENTREGA", style=discord.ButtonStyle.success)
    async def autorizar(self, interaction: discord.Interaction, _):
        semanas = carregar_json(SEMANA_FILE, {})
        historico = carregar_json(HISTORICO_FILE, [])

        semanas.setdefault(str(self.member.id), [])

        semanas_quitadas = self.quantidade // self.meta

        for _ in range(semanas_quitadas):
            semanas[str(self.member.id)].append(semana_atual())

        adv_removidos = min(semanas_quitadas - 1, get_adv(self.member.id))
        if adv_removidos > 0:
            remove_adv(self.member.id, adv_removidos)

        meta_concluida = self.quantidade >= self.meta

        promovido = False
        if self.primeira_farm and meta_concluida:
            cargo = discord.utils.get(self.member.guild.roles, name=CARGO_MEMBRO)
            if cargo and cargo not in self.member.roles:
                await self.member.add_roles(cargo)
                promovido = True

        historico.append({
            "usuario": str(self.member),
            "quantidade": self.quantidade,
            "primeira_farm": self.primeira_farm,
            "meta": self.meta,
            "meta_concluida": meta_concluida,
            "promovido": promovido,
            "adv_removidos": adv_removidos,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

        salvar_json(SEMANA_FILE, semanas)
        salvar_json(HISTORICO_FILE, historico)

        msg = (
            f"✅ **Entrega aprovada**\n"
            f"🎯 Meta: {'Concluída' if meta_concluida else f'Faltaram {self.meta - self.quantidade}'}\n"
        )

        if promovido:
            msg += "🔼 **Usuário promovido para MEMBRO**\n"

        msg += f"⚠ ADV removidos: **{adv_removidos}**"

        await interaction.response.send_message(msg, ephemeral=True)

# ================= MODAL =================
class EntregaModal(Modal):
    def __init__(self, meta):
        super().__init__(title="Entrega de Farm")
        self.meta = meta

        self.quantidade = TextInput(
            label="Quantidade entregue",
            placeholder="Ex: 800",
            required=True
        )

        self.para_quem = TextInput(
            label="Para quem entregou",
            placeholder="Nome / ID",
            required=True
        )

        self.primeira_farm = TextInput(
            label="1ª Farm? (Sim ou Não)",
            placeholder="Sim ou Não",
            required=True
        )

        self.add_item(self.quantidade)
        self.add_item(self.para_quem)
        self.add_item(self.primeira_farm)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value)
        except ValueError:
            return await interaction.response.send_message("❌ Quantidade inválida.", ephemeral=True)

        primeira = self.primeira_farm.value.lower() == "sim"

        semanas = carregar_json(SEMANA_FILE, {})
        if semana_atual() in semanas.get(str(interaction.user.id), []):
            return await interaction.response.send_message(
                "❌ Você já entregou nesta semana.", ephemeral=True
            )

        status = (
            "✅ Meta concluída"
            if qtd >= self.meta
            else f"❌ Faltaram {self.meta - qtd}"
        )

        embed = discord.Embed(
            title="📦 NOVA ENTREGA DE FARM",
            description=(
                f"👤 {interaction.user.mention}\n"
                f"📦 Quantidade: **{qtd}**\n"
                f"🤝 Para quem: **{self.para_quem.value}**\n"
                f"🌱 1ª Farm: **{'Sim' if primeira else 'Não'}**\n"
                f"🎯 {status}"
            ),
            color=discord.Color.orange()
        )

        await interaction.channel.send(
            embed=embed,
            view=EntregaView(interaction.user, self.meta, qtd, primeira)
        )

        await interaction.response.send_message(
            "📨 Sua entrega foi enviada para análise da staff.",
            ephemeral=True
        )

# ================= PAINEL =================
class TicketView(View):
    def __init__(self, meta):
        super().__init__(timeout=None)
        self.meta = meta

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(EntregaModal(self.meta))

# ================= COG =================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_semana.start()

    @tasks.loop(hours=24)
    async def verificar_semana(self):
        if datetime.now().weekday() != 6:
            return

        semanas = carregar_json(SEMANA_FILE, {})
        config = carregar_json(CONFIG_FILE, {})
        canal_adv = config.get("canal_advertencias")

        for guild in self.bot.guilds:
            canal = guild.get_channel(canal_adv) if canal_adv else None

            for member in guild.members:
                if any(r.name == CARGO_IGNORADO for r in member.roles):
                    continue

                if semana_atual() not in semanas.get(str(member.id), []):
                    adv = add_adv(member.id)

                    if canal:
                        await canal.send(
                            f"⚠ **ADVERTÊNCIA**\n👤 {member.mention}\nMotivo: Não entregou meta"
                        )

                    if adv >= LIMITE_ADV:
                        await member.kick(reason="5 advertências por falta de farm")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx, meta: int):
        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM",
            description="Clique no botão abaixo para entregar seu farm.",
            color=discord.Color.blurple()
        )

        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=TicketView(meta))
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def canaladv(self, ctx, canal: discord.TextChannel):
        config = carregar_json(CONFIG_FILE, {})
        config["canal_advertencias"] = canal.id
        salvar_json(CONFIG_FILE, config)
        await ctx.send("✅ Canal de advertências configurado.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))