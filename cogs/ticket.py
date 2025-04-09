import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os

class CloseConfirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="✅ Yes", style=discord.ButtonStyle.red)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("Closing ticket...")
        await interaction.channel.delete()

    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.gray)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket close canceled.", ephemeral=True)


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 CLOSE TICKET", style=discord.ButtonStyle.red)
    async def close_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=CloseConfirm(), ephemeral=True)


class TicketModal(discord.ui.Modal, title="Create a Ticket"):
    reason = discord.ui.TextInput(label="Reason", placeholder="Enter your reason...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, self.reason.value)


class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create a Ticket", style=discord.ButtonStyle.green)
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())


async def create_ticket(interaction, reason):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="Tickets")
    if category is None:
        category = await guild.create_category("Tickets")

    for channel in category.channels:
        if channel.name == f"ticket-{interaction.user.name.lower()}":
            return await interaction.response.send_message("You already have an open ticket!", ephemeral=True)

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

    embed = discord.Embed(
        title="📩 LARP Support",
        description=f"Reason: {reason}",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="Use the button below to close this ticket.")

    await ticket_channel.send(embed=embed, view=TicketControls())
    await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_panel", description="Send a ticket panel")
    async def panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Click the button below to create a ticket.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=TicketButton())

    @app_commands.command(name="ticket_transcript", description="Generate a ticket transcript")
    async def transcript_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

        messages = [f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}" async for msg in interaction.channel.history(limit=1000)]
        if not messages:
            return await interaction.response.send_message("No messages found in this ticket.", ephemeral=True)

        transcript = "\n".join(messages)
        file_path = f"transcript-{interaction.channel.name}.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        await interaction.response.send_message("Here is the ticket transcript:", file=discord.File(file_path))

        os.remove(file_path)

    @app_commands.command(name="ticket_open", description="Reopen a closed ticket")
    async def open_ticket(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name="Tickets")
        if not category:
            return await interaction.response.send_message("No ticket category found.", ephemeral=True)

        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name.lower()}",
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True),
            }
        )

        await interaction.response.send_message(f"Ticket reopened: {ticket_channel.mention}")

    @app_commands.command(name="ticket_close", description="Close the current ticket")
    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

        await interaction.response.send_message("Closing ticket...")
        await interaction.channel.delete()

    @app_commands.command(name="ticket_add", description="Add a user to a ticket")
    async def add_ticket(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

        await interaction.channel.set_permissions(user, view_channel=True, send_messages=True)
        await interaction.response.send_message(f"Added {user.mention} to the ticket.")

    @app_commands.command(name="ticket_remove", description="Remove a user from a ticket")
    async def remove_ticket(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.channel.name.startswith("ticket-"):
            return await interaction.response.send_message("This is not a ticket channel!", ephemeral=True)

        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(f"Removed {user.mention} from the ticket.")

    async def setup(self, bot):
        bot.tree.add_command(self.panel)
        bot.tree.add_command(self.transcript_ticket)
        bot.tree.add_command(self.open_ticket)
        bot.tree.add_command(self.close_ticket)
        bot.tree.add_command(self.add_ticket)
        bot.tree.add_command(self.remove_ticket)

def setup(bot):
    bot.add_cog(Ticket(bot))
