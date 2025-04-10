import discord
from discord import app_commands
from discord.ext import commands

class ApplicationSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="In-Game Moderator Application", description="Apply for the moderator role")
        ]
        super().__init__(placeholder="Select an application...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await self.cog.apply(interaction)  # Calls the apply command when an option is selected


class ApplicationMenu(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(ApplicationSelect(cog))


class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # ==== APPLICATION CONFIGURATION ====
        self.applications = {
            "In-Game Moderator Application": [
                "What is your discord username?",
                "What is your roblox username?",
                "Do you understand that asking for your application to be read will result in a denial?",
                "Explain what is RDM and the punishment for it.",
                "Explain what is VDM and the punishment for it.",
                "Explain what is LTAP and the punishment for it.",
                "Explain what is NITRP and the punishment for it.",
                "Explain what is Tool Abuse and the punishment for it.",
                "Do you understand that you have to go trough a training when your application gets accepted?",
                "Do you understand that requesting a role will result to a termination?",
                "Do you understand that you will be required to use SPaG?",
                "What is your timezone and do you have any questions?",
            ]
        }
        # ====================================

        self.response_channel_id = 1352595235976380508  # Stores the channel ID for application responses

    @app_commands.command(name="app_panel", description="Show available application")
    async def app_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Apply for a Position", description="Select an application from the menu below.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=ApplicationMenu(self), ephemeral=True)

    @app_commands.command(name="set_app_channel", description="Set the channel for application responses (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def set_app_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.response_channel_id = channel.id
        await interaction.response.send_message(f"Application responses will be sent to {channel.mention}.", ephemeral=True)

    async def apply(self, interaction: discord.Interaction):
        app_name = "In-Game Moderator Application"
        questions = self.applications[app_name]
        user = interaction.user
        answers = []

        if not self.response_channel_id:
            await interaction.response.send_message("Application response channel is not set.")
            return

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        try:
            await user.send(f"Starting your application for '{app_name}'. Please answer the following questions.")
            for question in questions:
                await user.send(f"**{question}**")
                msg = await self.bot.wait_for("message", check=check, timeout=120)
                answers.append(msg.content)
            
            # Format the response and send it to the chosen channel
            channel = self.bot.get_channel(self.response_channel_id)
            if not channel:
                await user.send("Application response channel not found.")
                return

            embed = discord.Embed(title=f"New Application: {app_name}", color=discord.Color.green())
            embed.add_field(name="User", value=user.mention, inline=False)
            for i, (q, a) in enumerate(zip(questions, answers), start=1):
                embed.add_field(name=f"Q{i}: {q}", value=a, inline=False)

            accept_button = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
            deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.danger)

            async def accept_callback(interaction: discord.Interaction):
                await self.send_modal(interaction, "Accepted")

            async def deny_callback(interaction: discord.Interaction):
                await self.send_modal(interaction, "Denied")

            accept_button.callback = accept_callback
            deny_button.callback = deny_callback

            view = discord.ui.View()
            view.add_item(accept_button)
            view.add_item(deny_button)

            await channel.send(embed=embed, view=view)
            await user.send("Your application has been submitted successfully!")

        except Exception:
            await user.send("Application process cancelled or an error occurred.")

    async def send_modal(self, interaction: discord.Interaction, status: str):
        modal = discord.ui.Modal(title=f"{status} Application", custom_id=f"{status.lower()}_modal")
        reason_input = discord.ui.TextInput(label="Reason for decision", style=discord.TextStyle.paragraph, placeholder="Enter the reason...", required=True)
        modal.add_item(reason_input)

        async def on_submit(interaction: discord.Interaction):
            reason = reason_input.value
            user = interaction.user
            # Send the reason to the user and log the decision
            await user.send(f"Your application has been {status}.\nReason: {reason}")

            # Log the decision in the admin channel
            embed = discord.Embed(title=f"Application {status}", color=discord.Color.green() if status == "Accepted" else discord.Color.red())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Reason", value=reason)
            admin_channel = self.bot.get_channel(self.response_channel_id)
            if admin_channel:
                await admin_channel.send(embed=embed)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(Applications(bot))
