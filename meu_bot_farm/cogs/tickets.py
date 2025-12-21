# BOT FARM KORTE — FINAL
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
    def __init__(self, user, qtd, meta, canal_aceitos, canal_adv):
        super().__init__(timeout=None)
        self.user = user
        self.qtd = qtd
        self.meta = meta
        self.canal_aceitos = canal_aceitos
        self.canal_adv = canal_adv

    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        entregas = load_json(ENTREGAS_FILE, {})
        advs = load_json(ADV_FILE, {})

        entregas[str(self.user.id)] = entregas.get(str(self.user.id), 0) + self.qtd

        # Embed aprovado
        embed = interaction.message.embeds[0]
        embed.set_field_at(
            index=4,
            name="📊 Status da Meta",
            value="✅ Meta concluída",
            inline=False
        )

        canal = interaction.guild.get_channel(self.canal_aceitos)
        if canal:
            await canal.send(embed=embed)

        # Remoção de ADV por compensação
        if str(self.user.id) in advs and entregas[str(self.user.id)] >= self.meta * 2:
            advs.pop(str(self.user.id))
            adv_canal = interaction.guild.get_channel(self.canal_adv)
            if adv_canal:
                msg = await adv_canal.send(
                    f"🔄 ADV removido por compensação — {self.user.mention}"
                )
                await asyncio.sleep(10)
                await msg.delete()

        save_json(ENTREGAS_FILE, entregas)
        save_json(ADV_FILE, advs)

        await interaction.message.delete()
        await interaction.response.send_message("Entrega aceita.", ephemeral=True)

# ================== MODAL ==================
class EntregaModal(Modal):
    def __init__(self, canal_analise, canal_aceitos, canal_adv, meta):
        super().__init__(title="Entrega de Farm – KORTE")
        self.canal_analise = canal_analise
        self.canal_aceitos = canal_aceitos
        self.canal_adv = canal_adv
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
            return

        if qtd >= self.meta:
            status = "✅ Meta concluída"
        else:
            falta = self.meta - qtd
            status = f"❌ Meta incompleta — faltam {falta}"

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            color=discord.Color.orange()
        )

        embed.add_field(name="👤 Quem entregou", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=str(qtd), inline=False)
        embed.add_field(name="📍 Entregou para", value=self.para.value, inline=False)
        embed.add_field(name="📅 Data", value=self.data.value, inline=False)
        embed.add_field(name="📊 Status da Meta", value=status, inline=False)

        canal = interaction.guild.get_channel(self.canal_analise)
        if canal:
            await canal.send(
                embed=embed,
                view=AnaliseView(
                    interaction.user,
                    qtd,
                    self.meta,
                    self.canal_aceitos,
                    self.canal_adv
                )
            )

        msg = await interaction.channel.send(
            f"{interaction.user.mention}, sua entrega foi enviada para análise da **Staff KORTE**."
        )
        await asyncio.sleep(30)
        await msg.delete()

# ================== PAINEL ==================
class PainelView(View):
    def __init__(self, canal_analise, canal_aceitos, canal_adv, meta):
        super().__init__(timeout=None)
        self.canal_analise = canal_analise
        self.canal_aceitos = canal_aceitos
        self.canal_adv = canal_adv
        self.meta = meta

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(
                self.canal_analise,
                self.canal_aceitos,
                self.canal_adv,
                self.meta
            )
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
            description="Clique no botão abaixo para entregar seu farming.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(
            embed=embed,
            view=PainelView(
                canal_analise.id,
                canal_aceitos.id,
                canal_adv.id,
                meta
            )
        )
        await ctx.message.delete()

# ================== SETUP ==================
async def setup(bot):
    await bot.add_cog(KorteFarm(bot))