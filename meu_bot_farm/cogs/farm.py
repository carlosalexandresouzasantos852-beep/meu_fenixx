from discord.ext import commands

class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong funcionando")

    @commands.command()
    async def meta(self, ctx, quantidade: int):
        await ctx.send(f"🎯 Meta definida: {quantidade}")

    @commands.command()
    async def entrega(self, ctx, quantidade: int):
        await ctx.send(f"📦 Entrega registrada: {quantidade}")

async def setup(bot):
    await bot.add_cog(Farm(bot))