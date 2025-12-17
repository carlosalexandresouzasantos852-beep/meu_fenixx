from discord.ext import commands
import discord

CARGO_INICIAL = "aviãozinho"
CARGO_FINAL = "membro"

class Cargos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def promover(self, ctx, membro: discord.Member):
        cargo_inicial = discord.utils.get(ctx.guild.roles, name=CARGO_INICIAL)
        cargo_final = discord.utils.get(ctx.guild.roles, name=CARGO_FINAL)

        if cargo_inicial in membro.roles:
            await membro.remove_roles(cargo_inicial)
            await membro.add_roles(cargo_final)
            await ctx.send(f"🎉 {membro.mention} promovido para **{CARGO_FINAL}**")

async def setup(bot):
    await bot.add_cog(Cargos(bot))