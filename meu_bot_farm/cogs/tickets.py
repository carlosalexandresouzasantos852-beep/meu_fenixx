import discord
import asyncio
from discord.ext import commands
from discord.ui import View, Modal, TextInput

CARGO_INICIAL = "aviãozinho"
CARGO_FINAL = "membro"
TEMPO_APAGAR_RECUSADO = 36000  # 10 horas


# ================== VIEW DE APROVAÇÃO (STAFF) ==================
class EntregaView(View):
    def __init__(self, member, dados, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.member = member
        self.dados = dados
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados
        self.mensagem_original = None

    def gerar_embed_final(self, promovido: bool):
        embed = discord.Embed(
            title="📦 Entrega Avaliada",
            color=discord.Color.green() if self.dados["meta_concluida"] else discord.Color.orange()
        )

        embed.add_field(name="👤 Usuário que entregou", value=self.member.mention, inline=False)
        embed.add_field(name="📥 Entregue para", value=self.dados["entregue_para"], inline=False)
        embed.add_field(name="📦 Quantidade", value=str(self.dados["quantidade"]), inline=True)
        embed.add_field(
            name="🆕 Primeiro farm",
            value="Sim" if self.dados["primeiro_farm"] else "Não",
            inline=True
        )

        if self.dados["meta_concluida"]:
            embed.add_field(name="🎯 Status da Meta", value="✅ Meta concluída", inline=False)
        else:
            embed.add_field(
                name="🎯 Status da Meta",
                value=f"⚠️ Faltam **{self.dados['faltante']}** para concluir",
                inline=False
            )

        if promovido:
            embed.add_field(
                name="🔼 Observação",
                value=f"{self.member.mention} foi **promovido para membro** 🎉",
                inline=False
            )

        return embed

    @discord.ui.button(label="✅ Autorizar Entrega", style=discord.ButtonStyle.success)
    async def autorizar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        if self.mensagem_original:
            await self.mensagem_original.delete()

        guild = interaction.guild
        promovido = False

        if self.dados["primeiro_farm"]:
            cargo_inicial = discord.utils.get(guild.roles, name=CARGO_INICIAL)
            cargo_final = discord.utils.get(guild.roles, name=CARGO_FINAL)

            if cargo_inicial and cargo_inicial in self.member.roles:
                await self.member.remove_roles(cargo_inicial)
            if cargo_final:
                await self.member.add_roles(cargo_final)

            promovido = True

        embed = self.gerar_embed_final(promovido)
        await self.canal_aceitos.send(embed=embed)

        aviso = await interaction.channel.send("✅ **Entrega analisada com sucesso.**")
        await asyncio.sleep(6)
        await aviso.delete()

        self.stop()

    @discord.ui.button(label="❌ Recusar Entrega", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        if self.mensagem_original:
            await self.mensagem_original.delete()

        embed = discord.Embed(
            title="📦 Entrega Recusada",
            description=f"{self.member.mention} teve a entrega **recusada** ❌",
            color=discord.Color.red()
        )

        msg = await self.canal_recusados.send(embed=embed)

        aviso = await interaction.channel.send("❌ **Entrega analisada com sucesso.**")
        await asyncio.sleep(6)
        await aviso.delete()

        await asyncio.sleep(TEMPO_APAGAR_RECUSADO)
        await msg.delete()

        self.stop()


# ================== MODAL ==================
class EntregaModal(Modal):
    def __init__(self, meta, canal_abertos, canal_aceitos, canal_recusados):
        super().__init__(title="Entrega de Farm")
        self.meta = meta
        self.canal_abertos = canal_abertos
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

        self.quantidade = TextInput(label="Quantidade entregue", required=True)
        self.entregue_para = TextInput(label="Entregue para quem?", required=True)
        self.primeiro_farm = TextInput(label="Primeiro farm? (sim/não)", required=True)

        self.add_item(self.quantidade)
        self.add_item(self.entregue_para)
        self.add_item(self.primeiro_farm)

    async def on_submit(self, interaction: discord.Interaction):
        # 🔥 CORREÇÃO PRINCIPAL (remove o erro "algo deu errado")
        await interaction.response.defer(ephemeral=True)

        try:
            qtd = int(self.quantidade.value)
        except ValueError:
            await interaction.followup.send("❌ Quantidade inválida.", ephemeral=True)
            return

        primeiro = self.primeiro_farm.value.lower() == "sim"
        meta_concluida = qtd >= self.meta

        dados = {
            "quantidade": qtd,
            "entregue_para": self.entregue_para.value,
            "primeiro_farm": primeiro,
            "meta_concluida": meta_concluida,
            "faltante": max(self.meta - qtd, 0)
        }

        embed = discord.Embed(
            title="📦 Nova Entrega para Aprovação",
            color=discord.Color.orange()
        )
        embed.add_field(name="Usuário", value=interaction.user.mention, inline=False)
        embed.add_field(name="Quantidade", value=str(qtd), inline=True)
        embed.add_field(name="Primeiro farm", value="Sim" if primeiro else "Não", inline=True)

        view = EntregaView(
            interaction.user,
            dados,
            self.canal_aceitos,
            self.canal_recusados
        )

        msg = await self.canal_abertos.send(embed=embed, view=view)
        view.mensagem_original = msg

        aviso = await interaction.followup.send(
            "📨 **Entrega enviada para aprovação da staff.**"
        )
        await asyncio.sleep(5)
        await aviso.delete()


# ================== VIEW DO PAINEL ==================
class TicketView(View):
    def __init__(self, meta, canal_abertos, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.meta = meta
        self.canal_abertos = canal_abertos
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EntregaModal(
                self.meta,
                self.canal_abertos,
                self.canal_aceitos,
                self.canal_recusados
            )
        )


# ================== COG ==================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(
        self,
        ctx,
        meta: int,
        canal_abertos: discord.TextChannel,
        canal_aceitos: discord.TextChannel,
        canal_recusados: discord.TextChannel
    ):
        embed = discord.Embed(
            title="🎫 TICKET ENTREGA DE FARM FXP",
            description="Clique no botão abaixo para registrar sua entrega.",
            color=discord.Color.blurple()
        )

        await ctx.send(
            embed=embed,
            view=TicketView(meta, canal_abertos, canal_aceitos, canal_recusados)
        )
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Tickets(bot))