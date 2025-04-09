import discord
from discord import app_commands
from discord.ext import commands

ROLE_PERMISSIONS = {
    "IA": 1352987568051851276,  # Replace with actual role ID
    "Management": 1352987681063436428,  # Replace with actual role ID
    "Foundership": 1352987799212654697,  # Replace with actual role ID
    "General": 1352982058586210304  # Replace with actual role ID
}

class TicketModal(discord.ui.Modal, title="LARP Support Ticket"):
    reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.long, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")
        if not category:
            category = await guild.create_category("Tickets")

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}", category=category
        )

        support_type = self.title.split(" - ")[1] if " - " in self.title else "General"
        allowed_role = guild.get_role(ROLE_PERMISSIONS.get(support_type))
        if allowed_role:
            await ticket_channel.set_permissions(guild.default_role, read_messages=False)
            await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            await ticket_channel.set_permissions(allowed_role, read_messages=True, send_messages=True)

        embed = discord.Embed(title="LARP Support", color=discord.Color.blue())
        embed.add_field(name="Reason:", value=self.reason.value, inline=False)
        embed.set_footer(text="Use the button below to close this ticket.")
        
        close_button = discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.danger)
        async def close_callback(inter: discord.Interaction):
            confirm_view = CloseConfirmView(ticket_channel)
            await inter.response.send_message("Are you sure you want to close this ticket?", view=confirm_view, ephemeral=True)
        close_button.callback = close_callback
        
        view = discord.ui.View()
        view.add_item(close_button)

        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)

class CloseConfirmView(discord.ui.View):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.channel.delete()
        await interaction.response.send_message("Ticket closed.", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket closure cancelled.", ephemeral=True)

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="IA", description="Report a staff member"),
            discord.SelectOption(label="Management", description="Support for management issues"),
            discord.SelectOption(label="Foundership", description="Highly important matters"),
            discord.SelectOption(label="General", description="Questions or issues"),
        ]
        super().__init__(placeholder="Choose a support type", options=options)

    async def callback(self, interaction: discord.Interaction):
        modal = TicketModal(title=f"LARP Support - {self.values[0]}")
        await interaction.response.send_modal(modal)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TicketDropdown())

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket_panel", description="Creates the LARP Support Panel")
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="LARP Support Panel", 
            description="Choose a support type in the following menu", 
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=TicketView())
    
    @app_commands.command(name="ticket_open", description="Manually open a ticket")
    async def ticket_open(self, interaction: discord.Interaction, category: str):
        modal = TicketModal(title=f"LARP Support - {category}")
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="ticket_close", description="Close the current ticket")
    async def ticket_close(self, interaction: discord.Interaction):
        confirm_view = CloseConfirmView(interaction.channel)
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=confirm_view, ephemeral=True)
    
    @app_commands.command(name="ticket_add", description="Add a user to a ticket")
    async def ticket_add(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"{member.mention} has been added to the ticket.", ephemeral=True)
    
    @app_commands.command(name="ticket_remove", description="Remove a user from a ticket")
    async def ticket_remove(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.channel.set_permissions(member, overwrite=None)
        await interaction.response.send_message(f"{member.mention} has been removed from the ticket.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
