from flask import Flask, render_template, request, redirect, session, flash
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
from supabase import create_client
import os
from dotenv import load_dotenv
#from utils.amazon_price import get_amazon_price
import requests

requests.post("https://amazon-price-worker.onrender.com")

load_dotenv()


app = Flask(__name__)
app.secret_key = SECRET_KEY

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


import re

def tokenize(text):
    if not text:
        return set()
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return set(text.split())

def similarity_score(title_a, title_b):
    a = tokenize(title_a)
    b = tokenize(title_b)
    if not a or not b:
        return 0
    return len(a & b)


# ---------------- HOME ----------------
@app.route("/")
def home():
    niches = (
        supabase
        .table("niches")
        .select("name, logo")
        .execute()
        .data
    )

    featured = (
        supabase.table("products")
        .select("*")
        .eq("is_featured", True)
        .limit(10)
        .execute()
        .data
    )

    return render_template(
        "home.html",
        niches=niches,
        featured=featured
    )



# ---------------- DELETE NICHE ----------------
@app.route("/admin/delete-niche/<niche>")
def delete_niche(niche):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    # count products in this niche FIRST
    count = (
        supabase.table("products")
        .select("id", count="exact")
        .eq("niche", niche)
        .execute()
        .count
    )

    # block deletion if products exist
    if count > 0:
        flash("Delete all products in this niche first.")
        return redirect("/admin/panel")

    # safe to delete niche
    supabase.table("niches").delete().eq("name", niche).execute()

    return redirect("/admin/panel")



# ---------------- EDIT NICHE ----------------
@app.route("/admin/edit-niche", methods=["POST"])
def edit_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    old = request.form["old_niche"]
    new = slugify(request.form["new_niche"])

    supabase.table("niches").update({"name": new}).eq("name", old).execute()
    supabase.table("products").update({"niche": new}).eq("niche", old).execute()

    return redirect("/admin/panel")


# ---------------- UPDATE NICHE LOGO ----------------
@app.route("/admin/update-niche-logo", methods=["POST"])
def update_niche_logo():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    niche = request.form["niche"]
    logo = request.form.get("logo") or None

    supabase.table("niches").update({
        "logo": logo
    }).eq("name", niche).execute()

    return redirect("/admin/panel")


# ---------------- NICHE PAGE ----------------
@app.route("/niche/<name>")
def niche(name):
    sub = request.args.get("sub", "all")

    products = (
        supabase.table("products")
        .select("*")
        .eq("niche", name)
        .execute()
        .data
    )

    if sub != "all":
        products = [p for p in products if p.get("sub_niche") == sub]

    sub_niches = (
        supabase.table("sub_niches")
        .select("name")
        .eq("niche", name)
        .execute()
        .data
    )

    return render_template(
        "niche.html",
        niche=name,
        products=products,
        sub_niches=["all"] + [s["name"] for s in sub_niches],
        active_sub=sub
    )

# @app.route("/niche/<name>")
# def niche(name):
#     products = (
#         supabase.table("products")
#         .select("*")
#         .eq("niche", name)
#         .eq("is_featured", False)
#         .execute()
#         .data
#     )
#
#     return render_template("niche.html", niche=name, products=products)


# ---------------- PRODUCT DETAIL PAGE ----------------
# @app.route("/niche/<niche>/<product_id>")
# def product_detail(niche, product_id):
#     product = (
#         supabase.table("products")
#         .select("*")
#         .eq("id", product_id)
#         .single()
#         .execute()
#         .data
#     )
#
#     if not product:
#         return redirect("/")
#
#     images = []
#
#     if product.get("extra_image_1"):
#         images.append(product["extra_image_1"])
#     if product.get("extra_image_2"):
#         images.append(product["extra_image_2"])
#     if product.get("extra_image_3"):
#         images.append(product["extra_image_3"])
#
#     return render_template(
#         "product_detail.html",
#         product=product,
#         niche=niche,
#         images=images
#     )
@app.route("/niche/<niche>/<product_id>")
def product_detail(niche, product_id):

    product = (
        supabase.table("products")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
        .data
    )

    if not product:
        return redirect("/")

    # Fetch same-niche products except current
    candidates = (
        supabase.table("products")
        .select("id, title, image, price, niche")
        .eq("niche", niche)
        .neq("id", product_id)
        .execute()
        .data
    )

    # Score by title similarity
    scored = [
        {
            **p,
            "score": similarity_score(product["title"], p["title"])
        }
        for p in candidates
    ]

    # Sort by similarity score (desc)
    similar = sorted(
        scored,
        key=lambda x: x["score"],
        reverse=True
    )

    # Take top 3 meaningful matches
    related = [p for p in similar if p["score"] > 0][:3]

    return render_template(
        "product_detail.html",
        product=product,
        niche=niche,
        images=[
            img for img in [
                product.get("extra_image_1"),
                product.get("extra_image_2"),
                product.get("extra_image_3")
            ] if img
        ],
        related=related
    )


# ---------------- SAVED ----------------
@app.route("/saved")
def saved():
    return render_template("saved.html")


# ---------------- CONTACT ----------------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form["username"] == ADMIN_USERNAME and
            request.form["password"] == ADMIN_PASSWORD
        ):
            session["admin"] = ADMIN_USERNAME
            return redirect("/admin/panel")

    return render_template("admin_login.html")


# ---------------- ADMIN PANEL ----------------
@app.route("/admin/panel")
def admin_panel():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    # Fetch niches
    niches = supabase.table("niches").select("name, logo").execute().data
    niche_names = [n["name"] for n in niches]

    # Fetch sub-niches
    sub_data = supabase.table("sub_niches").select("niche, name").execute().data
    sub_niches = {}

    for s in sub_data:
        sub_niches.setdefault(s["niche"], []).append(s["name"])

    # Fetch products
    products = supabase.table("products").select("*").execute().data

    # Group products by niche
    grouped = {n: [] for n in niche_names}
    for p in products:
        grouped.setdefault(p["niche"], []).append(p)

    return render_template(
        "admin_panel.html",
        products=grouped,
        niches=niches,
        sub_niches=sub_niches
    )



# ---------------- ADD NICHE ----------------

import re

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


@app.route("/admin/add-niche", methods=["POST"])
def add_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    raw = request.form["niche"]
    niche = slugify(raw)

    supabase.table("niches").insert({
        "name": niche,
        "logo": request.form.get("logo")
    }).execute()

    return redirect("/admin/panel")



# ---------------- ADD PRODUCT ----------------
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("products").insert({
        "niche": request.form["niche"],
        "title": request.form["title"],
        "price": request.form["price"],
        "image": request.form["image"],
        "link": request.form["link"],
        "description": "",
        "extra_images": "",
        "is_featured": False
    }).execute()

    return redirect("/admin/panel")




# ---------------- TOGGLE FEATURE ----------------
@app.route("/admin/toggle-feature/<product_id>")
def toggle_feature(product_id):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    product = (
        supabase.table("products")
        .select("is_featured")
        .eq("id", product_id)
        .single()
        .execute()
        .data
    )

    supabase.table("products").update({
        "is_featured": not product["is_featured"]
    }).eq("id", product_id).execute()

    return redirect("/admin/panel")

# # ---------------- FEATURE PRODUCT ----------------
# @app.route("/admin/feature", methods=["POST"])
# def feature_product():
#     if session.get("admin") != ADMIN_USERNAME:
#         return redirect("/admin")
#
#     supabase.table("products").insert({
#         "niche": "featured",
#         "title": request.form["title"],
#         "price": request.form["price"],
#         "image": request.form["image"],
#         "link": request.form["link"],
#         "is_featured": True
#     }).execute()
#
#     return redirect("/")




# ---------------- DELETE PRODUCT ----------------
@app.route("/admin/delete-product/<niche>/<product_id>")
def delete_product(niche, product_id):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("products").delete().eq("id", product_id).execute()
    return redirect("/admin/panel")


# ---------------- EDIT PRODUCT ----------------
@app.route("/admin/edit-product/<niche>/<product_id>", methods=["GET", "POST"])
def edit_product(niche, product_id):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    product = (
        supabase.table("products")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
        .data
    )

    if request.method == "POST":
        supabase.table("products").update({
            "title": request.form["title"],
            "price": request.form["price"],
            "image": request.form["image"],
            "link": request.form["link"],
            "description": request.form.get("description"),

            "extra_image_1": request.form.get("extra_image_1") or None,
            "extra_image_2": request.form.get("extra_image_2") or None,
            "extra_image_3": request.form.get("extra_image_3") or None,
        }).eq("id", product_id).execute()

        return redirect("/admin/panel")

    return render_template(
        "edit_product.html",
        product=product,
        niche=niche,
        index=product_id
    )


# ---------------- SEARCH PRODUCTS ----------------
@app.route("/search")
def search_products():
    query = request.args.get("q", "").strip()

    if not query:
        return redirect("/")

    results = (
        supabase.table("products")
        .select("*")
        .ilike("title", f"%{query}%")
        .execute()
        .data
    )

    return render_template(
        "search_results.html",
        query=query,
        products=results
    )


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip().lower()

    if len(query) < 2:
        return {"results": []}

    try:
        # 1️⃣ Fetch a SAFE subset (recent products only)
        response = (
            supabase
            .table("products")
            .select("id, title, image, niche")
            .execute()
        )

        products = response.data or []

        # 2️⃣ Python-side fuzzy filtering
        matches = [
            p for p in products
            if query in (p.get("title") or "").lower()
        ]

        # 3️⃣ Limit results
        matches = matches[:8]

        return {"results": matches}

    except Exception as e:
        print("SEARCH ERROR:", e)
        return {"results": []}




@app.route("/admin/add-sub-niche", methods=["POST"])
def add_sub_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("sub_niches").insert({
        "niche": request.form["niche"],
        "name": slugify(request.form["sub_niche"])
    }).execute()

    return redirect("/admin/panel")


@app.route("/admin/set-sub-niche", methods=["POST"])
def set_sub_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("products").update({
        "sub_niche": request.form["sub_niche"]
    }).eq("id", request.form["product_id"]).execute()

    return redirect("/admin/panel")


@app.route("/admin/delete-sub-niche/<niche>/<sub>")
def delete_sub_niche(niche, sub):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    # Move products back to 'all'
    supabase.table("products").update({
        "sub_niche": "all"
    }).eq("niche", niche).eq("sub_niche", sub).execute()

    # Delete sub-niche
    supabase.table("sub_niches").delete() \
        .eq("niche", niche) \
        .eq("name", sub) \
        .execute()

    return redirect("/admin/panel")



@app.route("/admin/update-prices", methods=["POST"])
def update_prices():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    products = (
        supabase.table("products")
        .select("id, link, price")
        .execute()
        .data
    )

    updated = 0

    for p in products:
        if not p.get("link"):
            continue

        new_price = get_amazon_price(p["link"])

        if new_price and new_price != p["price"]:
            supabase.table("products").update({
                "price": new_price
            }).eq("id", p["id"]).execute()

            updated += 1

    flash(f"✅ Prices updated successfully ({updated} products changed)")
    return redirect("/admin/panel")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
