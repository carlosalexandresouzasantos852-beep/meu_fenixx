import discord
import asyncio
import json
import os
from discord.ext import commands
from discord.ui import View, Modal, TextInput

print("🔥 TICKETS.PY KORTE CARREGADO 🔥")

CARGO_INICIAL = "aviãozinho"
CARGO_FINAL = "membro"
TEMPO_APAGAR_RECUSADO = 36000  # 10h

ARQUIVO_HISTORICO = "meu_bot_farm/data/historico.json"


# ================== HISTÓRICO ==================
def carregar_historico():
    if not os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)

    with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_historico(dados):
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def registrar_historico(user_id, aceito, primeiro_farm):
    historico = carregar_historico()
    uid = str(user_id)

    if uid not in historico:
        historico[uid] = {
            "total_entregas": 0,
            "aceitos": 0,
            "recusados": 0,
            "primeiro_farm": False
        }

    historico[uid]["total_entregas"] += 1

    if aceito:
        historico[uid]["aceitos"] += 1
    else:
        historico[uid]["recusados"] += 1

    if primeiro_farm:
        historico[uid]["primeiro_farm"] = True

    salvar_historico(historico)


# ================== VIEW DE APROVAÇÃO ==================
class EntregaView(View):
    def __init__(self, member, dados, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.member = member
        self.dados = dados
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados
        self.mensagem_original = None

    def embed_final(self, promovido):
        embed = discord.Embed(
            title="📦 Entrega Finalizada",
            color=discord.Color.green()
        )

        embed.add_field(name="👤 Usuário", value=self.member.mention, inline=False)
        embed.add_field(name="📦 Quantidade", value=self.dados["quantidade"], inline=True)
        embed.add_field(name="🆕 Primeiro Farm", value="Sim" if self.dados["primeiro_farm"] else "Não", inline=True)

        if self.dados["meta_concluida"]:
            embed.add_field(name="🎯 Meta", value="✅ Concluída", inline=False)
        else:
            embed.add_field(
                name="🎯 Meta",
                value=f"⚠️ Faltam {self.dados['faltante']}",
                inline=False
            )

        if promovido:
            embed.add_field(
                name="🔼 Promoção",
                value="Usuário promovido para **membro** 🎉",
                inline=False
            )

        return embed

    @discord.ui.button(label="✅ Autorizar Entrega", style=discord.ButtonStyle.success)
    async def autorizar(self, interaction: discord.Interaction, _):
        await interaction.response.defer(ephemeral=True)

        if self.mensagem_original:
            await self.mensagem_original.delete()

        promovido = False
        guild = interaction.guild

        # PROMOÇÃO SÓ SE: primeiro farm + meta concluída
        if self.dados["primeiro_farm"] and self.dados["meta_concluida"]:
            cargo_i = discord.utils.get(guild.roles, name=CARGO_INICIAL)
            cargo_f = discord.utils.get(guild.roles, name=CARGO_FINAL)

            if cargo_i and cargo_i in self.member.roles:
                await self.member.remove_roles(cargo_i)
            if cargo_f:
                await self.member.add_roles(cargo_f)

            promovido = True

        registrar_historico(self.member.id, True, self.dados["primeiro_farm"])

        await self.canal_aceitos.send(embed=self.embed_final(promovido))
        await interaction.followup.send("✅ Entrega autorizada.", ephemeral=True)

        self.stop()

    @discord.ui.button(label="❌ Recusar Entrega", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        await interaction.response.defer(ephemeral=True)

        if self.mensagem_original:
            await self.mensagem_original.delete()

        registrar_historico(self.member.id, False, self.dados["primeiro_farm"])

        embed = discord.Embed(
            title="❌ Entrega Recusada",
            description=self.member.mention,
            color=discord.Color.red()
        )

        msg = await self.canal_recusados.send(embed=embed)
        await interaction.followup.send("❌ Entrega recusada.", ephemeral=True)

        await asyncio.sleep(TEMPO_APAGAR_RECUSADO)
        await msg.delete()

        self.stop()


# ================== MODAL ==================
class EntregaModal(Modal):
    def __init__(self, meta, canal_abertos, canal_aceitos, canal_recusados):
        super().__init__(title="Entrega de Farm KORTE")

        self.meta = meta
        self.canal_abertos = canal_abertos
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

        self.quantidade = TextInput(label="Quantidade entregue")
        self.primeiro_farm = TextInput(label="Primeiro farm? (sim/não)")

        self.add_item(self.quantidade)
        self.add_item(self.primeiro_farm)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        qtd = int(self.quantidade.value)
        primeiro = self.primeiro_farm.value.lower() == "sim"

        dados = {
            "quantidade": qtd,
            "primeiro_farm": primeiro,
            "meta_concluida": qtd >= self.meta,
            "faltante": max(self.meta - qtd, 0)
        }

        embed = discord.Embed(
            title="📦 Nova Entrega para Avaliação",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Usuário", value=interaction.user.mention)
        embed.add_field(name="📦 Quantidade", value=qtd)
        embed.add_field(name="🆕 Primeiro Farm", value="Sim" if primeiro else "Não")

        view = EntregaView(interaction.user, dados, self.canal_aceitos, self.canal_recusados)
        msg = await self.canal_abertos.send(embed=embed, view=view)
        view.mensagem_original = msg

        await interaction.followup.send("📨 Entrega enviada para análise.", ephemeral=True)


# ================== PAINEL ==================
class TicketView(View):
    def __init__(self, meta, canal_abertos, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.meta = meta
        self.canal_abertos = canal_abertos
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(
            EntregaModal(self.meta, self.canal_abertos, self.canal_aceitos, self.canal_recusados)
        )


# ================== COG ==================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx, meta: int, canal_abertos: discord.TextChannel,
                     canal_aceitos: discord.TextChannel, canal_recusados: discord.TextChannel):

        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM KORTE",
            description="Clique no botão abaixo para registrar sua entrega.",
            color=discord.Color.blurple()
        )

        await ctx.send(embed=embed, view=TicketView(meta, canal_abertos, canal_aceitos, canal_recusados))
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def historico(self, ctx, membro: discord.Member):
        historico = carregar_historico()
        uid = str(membro.id)

        if uid not in historico:
            await ctx.send("📭 Usuário sem histórico.")
            return

        h = historico[uid]

        embed = discord.Embed(title="📊 Histórico de Farm", color=discord.Color.gold())
        embed.add_field(name="👤 Usuário", value=membro.mention, inline=False)
        embed.add_field(name="📦 Total", value=h["total_entregas"])
        embed.add_field(name="✅ Aceitos", value=h["aceitos"])
        embed.add_field(name="❌ Recusados", value=h["recusados"])
        embed.add_field(name="🆕 Primeiro Farm", value="Sim" if h["primeiro_farm"] else "Não")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tickets(bot))