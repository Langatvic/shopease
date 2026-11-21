// Cart-specific helpers (AJAX add to cart)
async function addToCart(productId, quantity = 1) {
  const form = new FormData();
  form.append('quantity', quantity);
  const res = await fetch(`/cart/add/${productId}/`, {
    method: 'POST',
    body: form,
    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
  });
  return res.json();
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}