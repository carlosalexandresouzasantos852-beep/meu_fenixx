import discord
import asyncio
import json
import os
from datetime import datetime
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput

print("🔥 SISTEMA DE FARM CARREGADO 🔥")

# ================= CONFIGURAÇÕES =================
CARGO_IGNORADO = "00"   # cargos ignorados do sistema
CARGO_MEMBRO = "membro"  # cargo padrão de membro
LIMITE_ADV = 5           # limite de advertências antes de expulsar

# Pastas e arquivos de dados
PASTA_DADOS = "meu_bot_farm/data"
HISTORICO_FILE = f"{PASTA_DADOS}/historico_farm.json"
ADV_FILE = f"{PASTA_DADOS}/advs.json"
SEMANA_FILE = f"{PASTA_DADOS}/semanas.json"
CONFIG_FILE = f"{PASTA_DADOS}/config.json"
LISTA_FILE = f"{PASTA_DADOS}/lista_membros.json"

# GIF do painel (substitua pelo seu link direto de GIF animado)
GIF_PAINEL = "https://cdn.discordapp.com/attachments/.../seu_gif.gif"

# ================= FUNÇÕES ÚTEIS =================
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

# ================= ADVERSIDADES =================
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

# ================= VIEW DE ENTREGA =================
class EntregaView(View):
    def __init__(self, member, quantidade, para_quem, data_entrega, meta, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.member = member
        self.quantidade = quantidade
        self.para_quem = para_quem
        self.data_entrega = data_entrega
        self.meta = meta
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    # Botão de ACEITAR
    @discord.ui.button(label="✅ ACEITAR", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.canal_aceitos)
        if canal:
            embed = discord.Embed(
                title="✅ ENTREGA ACEITA",
                description=(
                    f"👤 {self.member.mention}\n"
                    f"📦 Quantidade: **{self.quantidade}**\n"
                    f"🤝 Para quem: **{self.para_quem}**\n"
                    f"📅 Data: {self.data_entrega}\n"
                    f"🎯 Status da meta: {'Concluída' if self.quantidade >= self.meta else f'Faltaram {self.meta - self.quantidade}'}"
                ),
                color=discord.Color.green()
            )
            await canal.send(embed=embed)
        await interaction.message.delete()

    # Botão de RECUSAR
    @discord.ui.button(label="❌ RECUSAR", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, _):
        canal = interaction.guild.get_channel(self.canal_recusados)
        if canal:
            embed = discord.Embed(
                title="❌ ENTREGA RECUSADA",
                description=(
                    f"👤 {self.member.mention}\n"
                    f"📦 Quantidade: **{self.quantidade}**\n"
                    f"🤝 Para quem: **{self.para_quem}**\n"
                    f"📅 Data: {self.data_entrega}\n"
                    f"🎯 Status da meta: {'Concluída' if self.quantidade >= self.meta else f'Faltaram {self.meta - self.quantidade}'}"
                ),
                color=discord.Color.red()
            )
            await canal.send(embed=embed)
        await interaction.message.delete()

# ================= MODAL DE ENTREGA =================
class EntregaModal(Modal):
    def __init__(self, meta, canal_aceitos, canal_recusados):
        super().__init__(title="Entrega de Farm – Korte")
        self.meta = meta
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

        self.quantidade = TextInput(
            label="Quantidade entregue",
            placeholder="Ex: 800",
            required=True
        )
        self.para_quem = TextInput(
            label="Para quem entregou",
            placeholder="Ex: @Fulano",
            required=True
        )

        self.add_item(self.quantidade)
        self.add_item(self.para_quem)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value)
        except ValueError:
            return await interaction.response.send_message("❌ Quantidade inválida.", ephemeral=True)

        data_entrega = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Atualiza lista de membros
        lista = carregar_json(LISTA_FILE, {})
        lista[str(interaction.user.id)] = True  # marcou como entregou
        salvar_json(LISTA_FILE, lista)

        embed = discord.Embed(
            title="📦 NOVA ENTREGA DE FARM",
            description=(
                f"👤 {interaction.user.mention}\n"
                f"📦 Quantidade: **{qtd}**\n"
                f"🤝 Para quem: **{self.para_quem.value}**\n"
                f"📅 Data: {data_entrega}\n"
                f"🎯 Status da meta: {'Concluída' if qtd >= self.meta else f'Faltaram {self.meta - qtd}'}"
            ),
            color=discord.Color.orange()
        )

        await interaction.channel.send(
            embed=embed,
            view=EntregaView(interaction.user, qtd, self.para_quem.value, data_entrega, self.meta, self.canal_aceitos, self.canal_recusados)
        )

        msg = await interaction.response.send_message(
            "📨 Sua entrega foi enviada para análise da staff.",
            ephemeral=True
        )
        await asyncio.sleep(5)
        await msg.delete()

# ================= PAINEL DO TICKET =================
class TicketView(View):
    def __init__(self, meta, canal_aceitos, canal_recusados):
        super().__init__(timeout=None)
        self.meta = meta
        self.canal_aceitos = canal_aceitos
        self.canal_recusados = canal_recusados

    @discord.ui.button(label="📦 ENTREGAR FARM", style=discord.ButtonStyle.green)
    async def entregar(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(EntregaModal(self.meta, self.canal_aceitos, self.canal_recusados))

# ================= COG PRINCIPAL =================
class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verificar_semana.start()

    # Verificação semanal de entregas
    @tasks.loop(hours=24)
    async def verificar_semana(self):
        if datetime.now().weekday() != 6:  # domingo
            return

        lista = carregar_json(LISTA_FILE, {})
        config = carregar_json(CONFIG_FILE, {})
        canal_adv = config.get("canal_advertencias")

        for guild in self.bot.guilds:
            canal = guild.get_channel(canal_adv) if canal_adv else None
            for member in guild.members:
                if any(r.name == CARGO_IGNORADO for r in member.roles):
                    continue
                if not lista.get(str(member.id), False):
                    adv = add_adv(member.id)
                    if canal:
                        await canal.send(
                            f"⚠ **ADVERTÊNCIA**\n👤 {member.mention}\nMotivo: Não entregou a meta"
                        )
                    if adv >= LIMITE_ADV:
                        await member.kick(reason="5 advertências por falta de farm")

    # Comando para criar painel
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx, meta: int, canal_aceitos: discord.TextChannel, canal_recusados: discord.TextChannel):
        embed = discord.Embed(
            title="🎫 ENTREGA DE FARM – Corte",
            description="Clique no botão abaixo para entregar o farm.",
            color=discord.Color.blurple()
        )
        embed.set_image(url=GIF_PAINEL)
        await ctx.send(embed=embed, view=TicketView(meta, canal_aceitos.id, canal_recusados.id))
        await ctx.message.delete()

    # Comando para adicionar membros à lista de não entregues
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def add_lista(self, ctx, member: discord.Member):
        lista = carregar_json(LISTA_FILE, {})
        lista[str(member.id)] = False  # marcado como não entregou
        salvar_json(LISTA_FILE, lista)
        await ctx.send(f"✅ {member.mention} adicionado à lista de não entregues.")

# ================= SETUP =================
async def setup(bot):
    await bot.add_cog(Tickets(bot))