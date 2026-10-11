import streamlit as st
import pandas as pd
import base64
from pathlib import Path

# ==================== НАСТРОЙКИ СТРАНИЦЫ ====================
st.set_page_config(
    page_title="PhoneShop — премиум смартфоны",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== ПУТИ ====================
BASE = Path(__file__).parent
IMAGES_DIR = BASE / "data" / "images"

# ==================== ЗАГРУЗКА CSS ====================
def load_css(path: Path):
    if path.exists():
        st.markdown(
            f"<style>{path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

load_css(BASE / "assets" / "style.css")

# ==================== УТИЛИТЫ ====================
def format_price(value) -> str:
    """79990 → '79 990' (с неразрывными пробелами)."""
    return f"{int(value):,}".replace(",", " ")

def img_to_base64(pid: int):
    """Возвращает data-URI картинки или None, если файл не найден."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = IMAGES_DIR / f"{pid}.{ext}"
        if p.exists():
            mime = {"jpg": "jpeg", "jpeg": "jpeg",
                    "png": "png", "webp": "webp"}[ext]
            data = base64.b64encode(p.read_bytes()).decode()
            return f"data:image/{mime};base64,{data}"
    return None

# ==================== КОРЗИНА ====================
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ==================== ДАННЫЕ ====================
@st.cache_data
def load_phones():
    return pd.read_csv(BASE / "data" / "phones.csv")

phones = load_phones()

# ==================== HERO-СЕКЦИЯ ====================
st.markdown(
    """
    <h1 class="hero-title">📱 PhoneShop</h1>
    <p class="hero-subtitle">
        Премиальные смартфоны с доставкой за 1 день · Официальная гарантия · Рассрочка 0%
    </p>
    """,
    unsafe_allow_html=True,
)

# ==================== САЙДБАР — ФИЛЬТРЫ ====================
st.sidebar.markdown("## 🔍 Фильтры")

brands = ["Все"] + sorted(phones["brand"].unique().tolist())
selected_brand = st.sidebar.selectbox("Бренд", brands)

min_price, max_price = int(phones["price"].min()), int(phones["price"].max())
price_range = st.sidebar.slider(
    "Цена, ₽",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=1000,
)

min_ram = st.sidebar.select_slider(
    "Минимум ОЗУ, ГБ",
    options=[4, 6, 8, 12, 16],
    value=4,
)

only_in_stock = st.sidebar.checkbox("Только в наличии", value=True)
sort_by = st.sidebar.selectbox(
    "Сортировка",
    ["По популярности", "Цена ↑", "Цена ↓", "ОЗУ ↓"],
)

# ==================== ПРИМЕНЕНИЕ ФИЛЬТРОВ ====================
filtered = phones.copy()
if selected_brand != "Все":
    filtered = filtered[filtered["brand"] == selected_brand]

filtered = filtered[
    (filtered["price"] >= price_range[0]) &
    (filtered["price"] <= price_range[1]) &
    (filtered["ram"] >= min_ram)
]

if only_in_stock:
    filtered = filtered[filtered["in_stock"] == 1]

if sort_by == "Цена ↑":
    filtered = filtered.sort_values("price")
elif sort_by == "Цена ↓":
    filtered = filtered.sort_values("price", ascending=False)
elif sort_by == "ОЗУ ↓":
    filtered = filtered.sort_values("ram", ascending=False)

# ==================== КОРЗИНА В САЙДБАРЕ ====================
st.sidebar.divider()
st.sidebar.markdown("## 🛒 Корзина")

cart_count = sum(st.session_state.cart.values())
cart_total = 0
for pid, qty in st.session_state.cart.items():
    row = phones[phones["id"] == pid]
    if not row.empty:
        cart_total += int(row.iloc[0]["price"]) * qty

col_a, col_b = st.sidebar.columns(2)
col_a.metric("Товаров", cart_count)
col_b.metric("Сумма", f"{format_price(cart_total)} ₽")

if cart_count > 0 and st.sidebar.button("🗑 Очистить корзину", use_container_width=True):
    st.session_state.cart = {}
    st.rerun()

# ==================== ЛИНИЯ РЕЗУЛЬТАТОВ ====================
st.markdown(
    f"<div style='color:#A1A1AA;margin-bottom:12px;font-size:0.95rem'>"
    f"Найдено моделей: <b style='color:#C4B5FD'>{len(filtered)}</b>"
    f"</div>",
    unsafe_allow_html=True,
)

# ==================== КАТАЛОГ ====================
if filtered.empty:
    st.warning("😕 По вашим фильтрам ничего не найдено. Попробуйте изменить параметры.")
    st.stop()

COLS = 3
rows = [filtered.iloc[i:i + COLS] for i in range(0, len(filtered), COLS)]

for row in rows:
    cols = st.columns(COLS, gap="medium")
    for col, (_, phone) in zip(cols, row.iterrows()):
        pid = int(phone["id"])
        img_src = img_to_base64(pid)

        if img_src:
            img_html = f'<img src="{img_src}" alt="{phone["name"]}">'
        else:
            img_html = "<div style='font-size:64px;opacity:0.4'>📱</div>"

        in_stock = phone["in_stock"] == 1
        stock_html = "" if in_stock else "<div class='stock-out'>● Нет в наличии</div>"

        # ✅ Цену форматируем ЗАРАНЕЕ, чтобы не делать replace на всём HTML
        price_str = format_price(phone["price"])

        card_html = f"""
        <div class="phone-card">
            <div class="phone-img-wrap">{img_html}</div>
            <span class="brand-badge">{phone['brand']}</span>
            <div class="phone-name">{phone['name']}</div>
            <div class="phone-price">{price_str} <span class="currency">₽</span></div>
            {stock_html}
            <div class="phone-specs">
                <span class="spec-chip">🧠 {phone['ram']} ГБ</span>
                <span class="spec-chip">💾 {phone['storage']} ГБ</span>
                <span class="spec-chip">📺 {phone['screen']}"</span>
                <span class="spec-chip">📷 {phone['camera']} МП</span>
                <span class="spec-chip">🔋 {phone['battery']} мАч</span>
            </div>
        </div>
        """

        with col:
            st.markdown(card_html, unsafe_allow_html=True)

            if in_stock:
                if st.button(
                    "🛒 В корзину",
                    key=f"add_{pid}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + 1
                    st.toast(f"✅ {phone['name']} добавлен в корзину", icon="🛒")
                    st.rerun()
            else:
                st.button(
                    "Нет в наличии",
                    key=f"oos_{pid}",
                    disabled=True,
                    use_container_width=True,
                )

# ==================== КОРЗИНА ВНИЗУ ====================
if cart_count > 0:
    st.divider()
    st.markdown("## 🛒 Ваша корзина")

    cart_rows = []
    for pid, qty in st.session_state.cart.items():
        p = phones[phones["id"] == pid].iloc[0]
        cart_rows.append({
            "Товар": f"{p['brand']} {p['name']}",
            "Цена, ₽": format_price(p["price"]),
            "Кол-во": qty,
            "Итого, ₽": format_price(int(p["price"]) * qty),
        })

    st.dataframe(
        pd.DataFrame(cart_rows),
        use_container_width=True,
        hide_index=True,
    )

    total_str = format_price(cart_total)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#7C3AED,#EC4899);
                        padding:18px;border-radius:14px;text-align:center;">
                <div style="color:rgba(255,255,255,0.8);font-size:0.85rem">Итого</div>
                <div style="color:white;font-size:1.8rem;font-weight:800">
                    {total_str} ₽
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("✨ Оформить заказ", type="primary", use_container_width=True):
            st.session_state.cart = {}
            st.success("🎉 Заказ оформлен! Менеджер свяжется с вами.")
            st.balloons()

# ==================== FOOTER ====================
st.markdown(
    """
    <div class="footer">
        <span class="floating">📱</span> PhoneShop © 2026 · сделано на Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)