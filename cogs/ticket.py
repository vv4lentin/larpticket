import discord
from discord.ext import commands
import datetime
import os

class CloseConfirm(discord.ui.View):
    """Confirmation view for closing a ticket"""
    def __init__(self, bot):
        super().__init__(timeout=30)
        self.bot = bot

    @discord.ui.button(label="✅ Yes", style=discord.ButtonStyle.red)
    async def confirm_close(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.channel.send("Closing ticket...")
        await interaction.channel.delete()

    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.gray)
    async def cancel_close(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Ticket close canceled.", ephemeral=True)


class TicketControls(discord.ui.View):
    """Ticket controls with a close button"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.red)
    async def close_ticket_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=CloseConfirm(self.bot), ephemeral=True)


class TicketModal(discord.ui.Modal):
    """Modal to collect reason when opening a ticket"""
    def __init__(self, bot):
        super().__init__(title="Create a Ticket")
        self.bot = bot
        self.reason = discord.ui.TextInput(label="Reason", placeholder="Enter your reason...", required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(self.bot, interaction, self.reason.value)


class TicketButton(discord.ui.View):
    """Panel button to create a ticket"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎫 Create a Ticket", style=discord.ButtonStyle.green)
    async def create_ticket_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.bot))


async def create_ticket(bot, interaction, reason):
    """Handles ticket creation"""
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="Tickets")
    if category is None:
        category = await guild.create_category("Tickets")

    # Check if user already has a ticket
    for channel in category.channels:
        if channel.name == f"ticket-{interaction.user.name.lower()}":
            return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

    # Create ticket channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
    }
    ticket_channel = await guild.create_text_channel(
        name=f"ticket-{interaction.user.name.lower()}",
        category=category,
        overwrites=overwrites
    )

    # Send LARP Support Embed
    embed = discord.Embed(
        title="📩 LARP Support",
        description=f"Reason: {reason}",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="Use the button below to close this ticket.")

    await ticket_channel.send(embed=embed, view=TicketControls(bot))
    await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_channels=True)
    @commands.slash_command(name="ticket", description="Ticket system commands")
    async def ticket(self, ctx):
        pass  # Base command, hidden from users

    @ticket.sub_command(name="panel", description="Send a ticket panel")
    async def panel(self, ctx):
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Click the button below to create a ticket.",
            color=discord.Color.blue()
        )
        await ctx.respond(embed=embed, view=TicketButton(self.bot))

    @ticket.sub_command(name="transcript", description="Generate a ticket transcript")
    async def transcript_ticket(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("This is not a ticket channel!", ephemeral=True)

        messages = [f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}" async for msg in ctx.channel.history(limit=1000)]
        if not messages:
            return await ctx.respond("No messages found in this ticket.", ephemeral=True)

        transcript = "\n".join(messages)
        file_path = f"transcript-{ctx.channel.name}.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        await ctx.respond("Here is the ticket transcript:", file=discord.File(file_path))

        os.remove(file_path)

    @ticket.sub_command(name="open", description="Reopen a closed ticket")
    async def open_ticket(self, ctx):
        category = discord.utils.get(ctx.guild.categories, name="Tickets")
        if not category:
            return await ctx.respond("No ticket category found.", ephemeral=True)

        ticket_channel = await ctx.guild.create_text_channel(
            name=f"ticket-{ctx.author.name.lower()}",
            category=category,
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
            }
        )

        await ctx.respond(f"Ticket reopened: {ticket_channel.mention}")

    @ticket.sub_command(name="close", description="Close the current ticket")
    async def close_ticket(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("This is not a ticket channel!", ephemeral=True)

        await ctx.respond("Closing ticket...")
        await ctx.channel.delete()

    @ticket.sub_command(name="add", description="Add a user to a ticket")
    async def add_ticket(self, ctx, user: discord.Member):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("This is not a ticket channel!", ephemeral=True)

        await ctx.channel.set_permissions(user, view_channel=True, send_messages=True)
        await ctx.respond(f"Added {user.mention} to the ticket.")

    @ticket.sub_command(name="remove", description="Remove a user from a ticket")
    async def remove_ticket(self, ctx, user: discord.Member):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.respond("This is not a ticket channel!", ephemeral=True)

        await ctx.channel.set_permissions(user, overwrite=None)
        await ctx.respond(f"Removed {user.mention} from the ticket.")

def setup(bot):
    bot.add_cog(Ticket(bot))
