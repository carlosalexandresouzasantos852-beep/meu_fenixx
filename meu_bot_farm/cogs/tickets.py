# BOT FARM KORTE — AUTOMÁTICO
# Python 3.11 | discord.py 2.4+

import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput

# ================== CONFIG ==================
MAX_ADV = 5
PASTA = "meu_bot_farm/data"
GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

os.makedirs(PASTA, exist_ok=True)

ENTREGAS_FILE = f"{PASTA}/entregas.json"
ADV_FILE = f"{PASTA}/advs.json"

CARGOS_VALIDOS = [
    "gerente geral", "gerente de elite", "gerente de recrutamento",
    "gerente de farm", "elite", "recrutador", "membro", "aviãozinho"
]

# ================== JSON ==================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== VIEW DE ANÁLISE ==================
class AnaliseView(View):
    def __init__(self, user_id, qtd, meta, adv_channel):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.qtd = qtd
        self.meta = meta
        self.adv_channel = adv_channel

    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        entregas = load_json(ENTREGAS_FILE, {})
        advs = load_json(ADV_FILE, {})

        entregas[str(self.user_id)] = entregas.get(str(self.user_id), 0) + self.qtd

        # Remoção de ADV por compensação
        if str(self.user_id) in advs:
            if entregas[str(self.user_id)] >= self.meta * 2:
                advs.pop(str(self.user_id))
                canal = interaction.guild.get_channel(self.adv_channel)
                if canal:
                    msg = await canal.send(f"🔄 ADV removido por compensação <@{self.user_id}>")
                    await asyncio.sleep(5)
                    await msg.delete()

        save_json(ENTREGAS_FILE, entregas)
        save_json(ADV_FILE, advs)

        await interaction.message.delete()
        await interaction.response.send_message("✅ Entrega aceita.", ephemeral=True)

    @discord.ui.button(label="❌ RECUSAR", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        await interaction.message.delete()
        await interaction.response.send_message("❌ Entrega recusada.", ephemeral=True)

# ================== MODAL ==================
class EntregaModal(Modal):
    def __init__(self, canal_analise, adv_channel, meta):
        super().__init__(title="Entrega de Farm – KORTE")
        self.canal_analise = canal_analise
        self.adv_channel = adv_channel
        self.meta = meta

        self.qtd = TextInput(label="Quantidade entregue", required=True)
        self.para = TextInput(label="Entregou para quem?", required=True)
        self.data = TextInput(label="Data (DD/MM)", required=True)

        self.add_item(self.qtd)
        self.add_item(self.para)
        self.add_item(self.data)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.qtd.value)
        except:
            return await interaction.response.send_message("Quantidade inválida.", ephemeral=True)

        # ===== STATUS DA META =====
        if qtd >= self.meta:
            status = "✅ Meta concluída"
        else:
            falta = self.meta - qtd
            status = f"❌ Meta incompleta\nFaltam R$ {falta}"

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            color=discord.Color.orange()
        )

        embed.add_field(name="👤 Quem entregou", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=f"R$ {qtd}", inline=False)
        embed.add_field(name="📍 Entregou para", value=self.para.value, inline=False)
        embed.add_field(name="📅 Data", value=self.data.value, inline=False)
        embed.add_field(name="📊 Status da Meta", value=status, inline=False)

        canal = interaction.guild.get_channel(self.canal_analise)
        if canal:
            await canal.send(
                embed=embed,
                view=AnaliseView(interaction.user.id, qtd, self.meta, self.adv_channel)
            )

        msg = await interaction.response.send_message(
            "📨 Sua entrega foi enviada para análise da Staff KORTE.",
            ephemeral=True
        )
        await asyncio.sleep(3)

# ================== PAINEL ==================
class PainelView(View):
    def __init__(self, canal_analise, adv_channel, meta):
        super().__init__(timeout=None)
        self.canal_analise = canal_analise
        self.adv_channel = adv_channel
        self.meta = meta

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(self.canal_analise, self.adv_channel, self.meta)
        )

# ================== COG ==================
class KorteFarm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(
        self,
        ctx,
        meta: int,
        canal_analise: discord.TextChannel,
        canal_aceitos: discord.TextChannel,
        canal_recusados: discord.TextChannel,
        canal_adv: discord.TextChannel
    ):

        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM – KORTE",
            description=f"Meta semanal: **R$ {meta}**\nClique abaixo para entregar seu farm.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(
            embed=embed,
            view=PainelView(canal_analise.id, canal_adv.id, meta)
        )
        await ctx.message.delete()

    @commands.command()
    async def advfarm(self, ctx):
        advs = load_json(ADV_FILE, {})
        if not advs:
            return await ctx.send("✅ Nenhuma advertência registrada.")
        texto = "\n".join([f"<@{u}> — {q} ADV" for u, q in advs.items()])
        await ctx.send(f"⚠️ **Advertências registradas:**\n{texto}")

# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(KorteFarm(bot))