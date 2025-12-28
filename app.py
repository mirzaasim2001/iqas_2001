from flask import Flask, render_template, request, redirect, session
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = SECRET_KEY

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


# ---------------- HOME ----------------
@app.route("/")
def home():
    niches = supabase.table("niches").select("name").execute().data
    featured = (
        supabase.table("products")
        .select("*")
        .eq("is_featured", True)
        .limit(6)
        .execute()
        .data
    )

    return render_template(
        "home.html",
        niches=[n["name"] for n in niches],
        featured=featured
    )


# ---------------- DELETE NICHE ----------------
@app.route("/admin/delete-niche/<niche>")
def delete_niche(niche):
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("niches").delete().eq("name", niche).execute()
    supabase.table("products").delete().eq("niche", niche).execute()

    return redirect("/admin/panel")


# ---------------- EDIT NICHE ----------------
@app.route("/admin/edit-niche", methods=["POST"])
def edit_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    old = request.form["old_niche"]
    new = request.form["new_niche"].lower()

    supabase.table("niches").update({"name": new}).eq("name", old).execute()
    supabase.table("products").update({"niche": new}).eq("niche", old).execute()

    return redirect("/admin/panel")


# ---------------- NICHE PAGE ----------------
@app.route("/niche/<name>")
def niche(name):
    products = (
        supabase.table("products")
        .select("*")
        .eq("niche", name)
        .eq("is_featured", False)
        .execute()
        .data
    )

    return render_template("niche.html", niche=name, products=products)


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

    products = supabase.table("products").select("*").execute().data
    grouped = {}

    for p in products:
        grouped.setdefault(p["niche"], []).append(p)

    return render_template("admin_panel.html", products=grouped)


# ---------------- ADD NICHE ----------------
@app.route("/admin/add-niche", methods=["POST"])
def add_niche():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    niche = request.form["niche"].lower()
    supabase.table("niches").insert({"name": niche}).execute()

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
        "is_featured": False
    }).execute()

    return redirect("/admin/panel")


# ---------------- FEATURE PRODUCT ----------------
@app.route("/admin/feature", methods=["POST"])
def feature_product():
    if session.get("admin") != ADMIN_USERNAME:
        return redirect("/admin")

    supabase.table("products").insert({
        "niche": "featured",
        "title": request.form["title"],
        "price": request.form["price"],
        "image": request.form["image"],
        "link": request.form["link"],
        "is_featured": True
    }).execute()

    return redirect("/")


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
            "link": request.form["link"]
        }).eq("id", product_id).execute()

        return redirect("/admin/panel")

    return render_template(
        "edit_product.html",
        product=product,
        niche=niche,
        index=product_id
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
