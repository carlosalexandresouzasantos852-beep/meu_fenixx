import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ext import commands
from discord.ui import View, Modal, TextInput

PASTA_DADOS = "meu_bot_farm/data"
os.makedirs(PASTA_DADOS, exist_ok=True)

# ========= CONFIG =========
GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

DADOS_FILE = f"{PASTA_DADOS}/entregas.json"

def carregar_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ========= VIEW STAFF =========
class AnaliseView(View):
    def __init__(self, dados, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.dados = dados
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.canal_aceitos)
        if canal:
            await canal.send(embed=interaction.message.embeds[0])
        await interaction.message.delete()
        await interaction.response.send_message("Entrega aceita.", ephemeral=True)

    @discord.ui.button(label="❌ RECUSAR", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.canal_recusados)
        if canal:
            await canal.send(embed=interaction.message.embeds[0])
        await interaction.message.delete()
        await interaction.response.send_message("Entrega recusada.", ephemeral=True)

# ========= MODAL =========
class EntregaModal(Modal):
    def __init__(self, meta, canal_analise, canal_aceitos, canal_recusados):
        super().__init__(title="Entrega de Farm – Corte")
        self.meta = meta
        self.canal_analise = canal_analise
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

        self.quantidade = TextInput(label="Quantidade entregue", required=True)
        self.entregou_para = TextInput(label="Entregou para quem?", required=True)
        self.data = TextInput(label="Data da entrega", placeholder="DD/MM/AAAA", required=True)

        self.add_item(self.quantidade)
        self.add_item(self.entregou_para)
        self.add_item(self.data)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value)
        except ValueError:
            return await interaction.response.send_message("❌ Quantidade inválida.", ephemeral=True)

        status = "✅ Meta concluída" if qtd >= self.meta else f"❌ Faltam {self.meta - qtd}"

        embed = discord.Embed(
            title="📦 ENTREGA DE FARM – KORTE",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Quem entregou", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=str(qtd), inline=True)
        embed.add_field(name="🎯 Meta", value=str(self.meta), inline=True)
        embed.add_field(name="📊 Status", value=status, inline=False)
        embed.add_field(name="📍 Entregou para", value=self.entregou_para.value, inline=False)
        embed.add_field(name="📅 Data", value=self.data.value, inline=False)

        canal = interaction.guild.get_channel(self.canal_analise)
        if canal:
            await canal.send(
                embed=embed,
                view=AnaliseView({}, self.canal_aceitos, self.canal_recusados)
            )

        msg = await interaction.response.send_message(
            "📨 Sua entrega foi enviada para análise da staff.",
            ephemeral=True
        )
        await asyncio.sleep(5)

# ========= VIEW PAINEL =========
class PainelView(View):
    def __init__(self, meta, canal_analise, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.meta = meta
        self.canal_analise = canal_analise
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(
                self.meta,
                self.canal_analise,
                self.canal_aceitos,
                self.canal_recusados
            )
        )

# ========= COG =========
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx, meta: int, canal_analise: discord.TextChannel,
                     canal_aceitos: discord.TextChannel,
                     canal_recusados: discord.TextChannel):

        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM – KORTE",
            description="Clique no botão abaixo para entregar o farm.",
            color=discord.Color.blurple()
        )

        embed.set_image(url=GIF_PAINEL)

        await ctx.send(
            embed=embed,
            view=PainelView(
                meta,
                canal_analise.id,
                canal_aceitos.id,
                canal_recusados.id
            )
        )
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))