import discord
import asyncio
import json
import os
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput

PASTA = "meu_bot_farm/data"
os.makedirs(PASTA, exist_ok=True)

ENTREGAS_FILE = f"{PASTA}/entregas.json"
ADV_FILE = f"{PASTA}/adv.json"

GIF_PAINEL = "https://cdn.discordapp.com/attachments/1266573285236408363/1452178207255040082/Adobe_Express_-_VID-20251221-WA0034.gif"

META_ADV = 3
CARGOS_IGNORADOS = ["01", "02", "03", "Dono", "Diretor", "Administrador"]

def load(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class AnaliseView(View):
    def __init__(self, aceitos, recusados):
        super().__init__(timeout=None)
        self.aceitos = aceitos
        self.recusados = recusados

    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.aceitos)
        await canal.send(embed=interaction.message.embeds[0])
        await interaction.message.delete()
        await interaction.response.send_message("Entrega aceita.", ephemeral=True)

    @discord.ui.button(label="❌ RECUSAR", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.recusados)
        await canal.send(embed=interaction.message.embeds[0])
        await interaction.message.delete()
        await interaction.response.send_message("Entrega recusada.", ephemeral=True)

class EntregaModal(Modal):
    def __init__(self, meta, analise, aceitos, recusados):
        super().__init__(title="Entrega de Farm – Corte")
        self.meta = meta
        self.analise = analise
        self.aceitos = aceitos
        self.recusados = recusados

        self.qtd = TextInput(label="Quantidade entregue")
        self.para = TextInput(label="Entregou para quem?")
        self.data = TextInput(label="Data (DD/MM/AAAA)")

        self.add_item(self.qtd)
        self.add_item(self.para)
        self.add_item(self.data)

    async def on_submit(self, interaction: discord.Interaction):
        qtd = int(self.qtd.value)
        entregas = load(ENTREGAS_FILE, {})
        entregas[str(interaction.user.id)] = qtd
        save(ENTREGAS_FILE, entregas)

        status = "✅ Meta concluída" if qtd >= self.meta else f"❌ Faltam {self.meta - qtd}"

        embed = discord.Embed(title="📦 ENTREGA DE FARM – CORTE", color=discord.Color.orange())
        embed.add_field(name="👤 Quem entregou", value=interaction.user.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=qtd)
        embed.add_field(name="🎯 Meta", value=self.meta)
        embed.add_field(name="📊 Status", value=status)
        embed.add_field(name="📍 Entregou para", value=self.para.value)
        embed.add_field(name="📅 Data", value=self.data.value)

        canal = interaction.guild.get_channel(self.analise)
        await canal.send(embed=embed, view=AnaliseView(self.aceitos, self.recusados))

        await interaction.response.send_message(
            "📨 Sua entrega foi enviada para análise da staff.",
            ephemeral=True
        )

class PainelView(View):
    def __init__(self, meta, analise, aceitos, recusados):
        super().__init__(timeout=None)
        self.meta = meta
        self.analise = analise
        self.aceitos = aceitos
        self.recusados = recusados

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(self.meta, self.analise, self.aceitos, self.recusados)
        )

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset_semanal.start()

    @commands.command()
    async def ticket(self, ctx, meta: int, analise: discord.TextChannel,
                     aceitos: discord.TextChannel,
                     recusados: discord.TextChannel,
                     advertencias: discord.TextChannel):

        self.bot.adv_channel = advertencias.id
        self.bot.meta = meta

        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM – CORTE",
            description="Clique no botão abaixo para entregar o farm.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)

        await ctx.send(embed=embed, view=PainelView(
            meta, analise.id, aceitos.id, recusados.id
        ))
        await ctx.message.delete()

    @tasks.loop(hours=1)
    async def reset_semanal(self):
        now = datetime.now()
        if now.weekday() == 0 and now.hour == 0:
            entregas = load(ENTREGAS_FILE, {})
            advs = load(ADV_FILE, {})

            guild = self.bot.guilds[0]
            canal = guild.get_channel(self.bot.adv_channel)

            for member in guild.members:
                if any(r.name in CARGOS_IGNORADOS for r in member.roles):
                    continue

                if str(member.id) not in entregas:
                    advs[str(member.id)] = advs.get(str(member.id), 0) + 1
                    await canal.send(f"⚠️ ADV aplicada a {member.mention}")

                    if advs[str(member.id)] >= META_ADV:
                        await member.kick(reason="ADV por não entregar farm")

            save(ADV_FILE, advs)
            save(ENTREGAS_FILE, {})

async def setup(bot):
    await bot.add_cog(Tickets(bot))