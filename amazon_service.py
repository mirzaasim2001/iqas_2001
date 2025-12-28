def fetch_trending_products(niche):
    """
    Later replace with:
    - Amazon API
    - Rainforest API
    - Playwright scraping
    """

    # MOCK DATA (structure is REAL)
    return [
        {
            "title": "Men Slim Fit Casual Shirt",
            "image": "https://m.media-amazon.com/images/I/81xyz.jpg",
            "price": "₹1,299",
            "link": "https://www.amazon.in/dp/XXXX?tag=your_affiliate_id"
        },
        {
            "title": "Women's Summer Dress",
            "image": "https://m.media-amazon.com/images/I/71abc.jpg",
            "price": "₹1,899",
            "link": "https://www.amazon.in/dp/YYYY?tag=your_affiliate_id"
        }
    ]

def search_amazon(query):
    return fetch_trending_products(query)
