import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- ⚙️ ตั้งค่าความปลอดภัย -----------------
# ดึง Token บอทจากระบบ Secrets / Environment Variables
TOKEN = os.getenv("DISCORD_TOKEN")

# ⚠️ เปลี่ยนตรงนี้เป็น Discord User ID ของคุณ (ตัวเลขล้วน) เพื่อรับซองเติมเงิน
ADMIN_ID = 123456789012345678  
# --------------------------------------------------------


# 📝 Modal หน้าต่างป๊อปอัปสำหรับกรอกซองทรูมันนี่
class TopupModal(Modal, title="💳 เติมเงินด้วยซองทรูมันนี่"):
    voucher_url = TextInput(
        label="ลิงก์ซองทรูมันนี่วอลเล็ท",
        placeholder="https://gift.truemoney.com/v1/?v=xxxxxx (ต้องใช้ซองที่ยังไม่หมดอายุ)",
        required=True,
        min_length=15
    )

    async def on_submit(self, interaction: discord.Interaction):
        url = self.voucher_url.value.strip()

        # แจ้งผู้ใช้ว่าส่งข้อมูลสำเร็จแล้ว
        await interaction.response.send_message(
            "✅ ส่งซองอั่งเปาเรียบร้อยแล้ว! ระบบได้ส่งข้อมูลให้แอดมินตรวจสอบแล้วครับ", 
            ephemeral=True
        )

        # ส่งลิงก์ซองทรูมันนี่ไปที่ DM ข้อความส่วนตัวของ Admin
        try:
            admin = await interaction.client.fetch_user(ADMIN_ID)
            if admin:
                embed_admin = discord.Embed(
                    title="🚨 แจ้งเตือนการเติมเงินใหม่!",
                    color=0xff9900
                )
                embed_admin.add_field(name="👤 ผู้ส่ง", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                embed_admin.add_field(name="🔗 ลิงก์ซองอั่งเปา", value=f"`{url}`", inline=False)
                
                await admin.send(embed=embed_admin)
        except Exception as e:
            print(f"❌ ไม่สามารถส่งข้อความหา Admin ได้: {e}")


# 🛒 View ยืนยันการสั่งซื้อ
class ConfirmPurchaseView(View):
    def __init__(self, product_name, price):
        super().__init__(timeout=60)
        self.product_name = product_name
        self.price = price

    @discord.ui.button(label="✅ ยืนยันการซื้อ", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        # ดึงยศชื่อ VIP ใน Server
        role = discord.utils.get(interaction.guild.roles, name="VIP")
        
        if role:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(
                    f"🎉 ยินดีด้วย! คุณได้รับยศ **{role.name}** เรียบร้อยแล้ว!", 
                    ephemeral=True
                )
            except Exception:
                await interaction.response.send_message(
                    "⚠️ บอทไม่มีสิทธิ์มอบยศนี้ (กรุณาเช็กสิทธิ์ Role ของบอทในเซิร์ฟเวอร์)", 
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"✅ คุณเลือกซื้อ **{self.product_name}** ราคา {self.price} บาท (กรุณาสร้างยศชื่อ 'VIP' ในเซิร์ฟเวอร์ด้วยครับ)", 
                ephemeral=True
            )

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("❌ ยกเลิกรายการสั่งซื้อเรียบร้อยแล้ว", ephemeral=True)


# 🔽 Select Menu เมนูเลือกสินค้า
class ProductSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="ยศ VIP", 
                value="vip_role", 
                description="ราคา 50 บาท | ยศสุดเท่พร้อมสิทธิ์พิเศษ", 
                emoji="👑"
            )
        ]
        super().__init__(placeholder="👉 คลิกที่นี่เพื่อเลือกสินค้า...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "vip_role":
            view = ConfirmPurchaseView(product_name="ยศ VIP", price=50)
            await interaction.response.send_message(
                "❓ **ยืนยันการสั่งซื้อ:** คุณต้องการซื้อ **ยศ VIP (ราคา 50฿)** ใช่หรือไม่?", 
                view=view, 
                ephemeral=True
            )


# 🔘 View ปุ่มกดหลักของหน้าร้านค้า
class ShopRoleView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 เติมเงิน", style=discord.ButtonStyle.green, custom_id="btn_topup")
    async def topup_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(TopupModal())

    @discord.ui.button(label="🛒 ซื้อสินค้า", style=discord.ButtonStyle.blurple, custom_id="btn_buy")
    async def buy_button(self, interaction: discord.Interaction, button: Button):
        view = View()
        view.add_item(ProductSelect())
        await interaction.response.send_message("🛒 **กรุณาเลือกสินค้าที่คุณต้องการสั่งซื้อ:**", view=view, ephemeral=True)


# ----------------- 🤖 คำสั่งบอท -----------------
@bot.event
async def on_ready():
    print(f'✅ บอท {bot.user} ออนไลน์พร้อมใช้งานแล้ว!')

@bot.command()
async def shop_role(ctx):
    embed = discord.Embed(
        title="🛒 ร้านค้าจำหน่ายยศอัตโนมัติ",
        description="ยินดีต้อนรับสู่ร้านค้า! กดปุ่มด้านล่างเพื่อเลือกซื้อสินค้าหรือเติมเงินได้เลยครับ",
        color=0x3498db
    )
    embed.add_field(
        name="👑 ยศ VIP",
        value="• **ราคา:** `50฿`\n• **รายละเอียด:** สิทธิ์ยศ VIP ประจำเซิร์ฟเวอร์",
        inline=False
    )
    embed.set_footer(text="ระบบชำระเงินผ่าน TrueMoney Wallet")

    await ctx.send(embed=embed, view=ShopRoleView())

# รันบอทโดยใช้ Token จาก Secrets
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ไม่พบ DISCORD_TOKEN กรุณาตั้งค่าใน Secrets ของ Replit ก่อนครับ")
