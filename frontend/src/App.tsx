import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api'

// Types
interface MenuItem {
  id: number
  name: string
  category: string
  price: number
  emoji: string
  is_available: boolean
  description: string
}

interface OrderItem {
  menu_item_id: number
  menu_item_name: string
  quantity: number
  unit_price: number
  subtotal: number
}

interface Order {
  id: number
  order_number: number
  customer_name: string
  status: string
  total: number
  tax: number
  is_paid: boolean
  items: OrderItem[]
  created_at: string
}

interface CartItem {
  menu_item: MenuItem
  quantity: number
}

interface QueueOrder {
  order_number: number
  customer_name: string
  status: string
  items_summary: string
  wait_time_minutes: number
}

interface DailySales {
  date: string
  total_orders: number
  total_revenue: number
  cash_total: number
  card_total: number
  total_tips: number
  top_items: { name: string; quantity: number; revenue: number }[]
}

type View = 'pos' | 'orders' | 'queue' | 'sales' | 'settings'

function App() {
  // State
  const [view, setView] = useState<View>('pos')
  const [menu, setMenu] = useState<MenuItem[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [customerName, setCustomerName] = useState('')
  const [orders, setOrders] = useState<Order[]>([])
  const [queue, setQueue] = useState<QueueOrder[]>([])
  const [dailySales, setDailySales] = useState<DailySales | null>(null)
  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState('')

  // Fetch menu
  const fetchMenu = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/menu?available_only=false`)
      const data = await res.json()
      setMenu(data)
      
      const cats = [...new Set(data.map((i: MenuItem) => i.category))]
      setCategories(cats as string[])
      if (cats.length > 0 && !selectedCategory) {
        setSelectedCategory(cats[0] as string)
      }
    } catch (err) {
      console.error('Failed to fetch menu:', err)
    }
  }, [selectedCategory])

  // Fetch orders
  const fetchOrders = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/orders?today_only=true`)
      const data = await res.json()
      setOrders(data)
    } catch (err) {
      console.error('Failed to fetch orders:', err)
    }
  }, [])

  // Fetch queue
  const fetchQueue = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/orders/queue`)
      const data = await res.json()
      setQueue(data)
    } catch (err) {
      console.error('Failed to fetch queue:', err)
    }
  }, [])

  // Fetch daily sales
  const fetchDailySales = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sales/daily`)
      const data = await res.json()
      setDailySales(data)
    } catch (err) {
      console.error('Failed to fetch sales:', err)
    }
  }, [])

  // Initial load and polling
  useEffect(() => {
    fetchMenu()
    fetchOrders()
    fetchQueue()
    
    const interval = setInterval(() => {
      fetchOrders()
      fetchQueue()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [fetchMenu, fetchOrders, fetchQueue])

  useEffect(() => {
    if (view === 'sales') {
      fetchDailySales()
    }
  }, [view, fetchDailySales])

  // Show notification
  const showNotification = (msg: string) => {
    setNotification(msg)
    setTimeout(() => setNotification(''), 2000)
  }

  // Add to cart
  const addToCart = (item: MenuItem) => {
    if (!item.is_available) return
    
    setCart(prev => {
      const existing = prev.find(c => c.menu_item.id === item.id)
      if (existing) {
        return prev.map(c =>
          c.menu_item.id === item.id
            ? { ...c, quantity: c.quantity + 1 }
            : c
        )
      }
      return [...prev, { menu_item: item, quantity: 1 }]
    })
  }

  // Remove from cart
  const removeFromCart = (itemId: number) => {
    setCart(prev => {
      const existing = prev.find(c => c.menu_item.id === itemId)
      if (existing && existing.quantity > 1) {
        return prev.map(c =>
          c.menu_item.id === itemId
            ? { ...c, quantity: c.quantity - 1 }
            : c
        )
      }
      return prev.filter(c => c.menu_item.id !== itemId)
    })
  }

  // Calculate cart total
  const cartSubtotal = cart.reduce((sum, c) => sum + c.menu_item.price * c.quantity, 0)
  const cartTax = cartSubtotal * 0.0875
  const cartTotal = cartSubtotal + cartTax

  // Submit order
  const submitOrder = async () => {
    if (cart.length === 0) return
    
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          items: cart.map(c => ({
            menu_item_id: c.menu_item.id,
            quantity: c.quantity
          }))
        })
      })
      
      if (res.ok) {
        const order = await res.json()
        showNotification(`Order #${order.order_number} created!`)
        setCart([])
        setCustomerName('')
        fetchOrders()
        fetchQueue()
      }
    } catch (err) {
      console.error('Failed to create order:', err)
    }
    setLoading(false)
  }

  // Update order status
  const updateOrderStatus = async (orderId: number, status: string) => {
    try {
      await fetch(`${API_BASE}/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      })
      fetchOrders()
      fetchQueue()
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }

  // Process payment
  const processPayment = async (orderId: number, method: 'cash' | 'card') => {
    const order = orders.find(o => o.id === orderId)
    if (!order) return
    
    try {
      await fetch(`${API_BASE}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          amount: order.total,
          method
        })
      })
      showNotification(`Payment received!`)
      fetchOrders()
    } catch (err) {
      console.error('Failed to process payment:', err)
    }
  }

  // Toggle item availability
  const toggleAvailability = async (itemId: number) => {
    try {
      await fetch(`${API_BASE}/menu/${itemId}/toggle-availability`, {
        method: 'PATCH'
      })
      fetchMenu()
    } catch (err) {
      console.error('Failed to toggle availability:', err)
    }
  }

  // Filtered menu
  const filteredMenu = menu.filter(m => m.category === selectedCategory)

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 px-4 py-3 flex items-center justify-between border-b border-gray-700">
        <h1 className="text-xl font-bold flex items-center gap-2">
          🌮 Food Truck POS
        </h1>
        <div className="text-sm text-gray-400">
          {new Date().toLocaleDateString()}
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-pulse">
          {notification}
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {/* POS View */}
        {view === 'pos' && (
          <div className="h-full flex flex-col lg:flex-row">
            {/* Menu Section */}
            <div className="flex-1 flex flex-col p-4 overflow-hidden">
              {/* Category tabs */}
              <div className="flex gap-2 mb-4 overflow-x-auto no-scrollbar pb-2">
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-4 py-2 rounded-full whitespace-nowrap capitalize font-medium transition-all ${
                      selectedCategory === cat
                        ? 'bg-truck-orange text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Menu grid */}
              <div className="flex-1 overflow-y-auto no-scrollbar">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {filteredMenu.map(item => (
                    <button
                      key={item.id}
                      onClick={() => addToCart(item)}
                      disabled={!item.is_available}
                      className={`menu-item-btn ${!item.is_available ? 'sold-out' : ''}`}
                    >
                      <div className="text-3xl mb-2">{item.emoji}</div>
                      <div className="font-semibold text-sm truncate">{item.name}</div>
                      <div className="text-truck-yellow font-bold">${item.price.toFixed(2)}</div>
                      {!item.is_available && (
                        <div className="text-xs text-red-400 mt-1">SOLD OUT</div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Cart Section */}
            <div className="lg:w-80 bg-gray-800 border-t lg:border-t-0 lg:border-l border-gray-700 flex flex-col">
              <div className="p-4 border-b border-gray-700">
                <input
                  type="text"
                  placeholder="Customer name (optional)"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-truck-orange"
                />
              </div>

              <div className="flex-1 overflow-y-auto p-4 no-scrollbar">
                {cart.length === 0 ? (
                  <div className="text-gray-500 text-center py-8">
                    Tap items to add to order
                  </div>
                ) : (
                  <div className="space-y-3">
                    {cart.map(c => (
                      <div key={c.menu_item.id} className="flex items-center justify-between bg-gray-700 rounded-lg p-3">
                        <div className="flex-1">
                          <div className="font-medium">{c.menu_item.emoji} {c.menu_item.name}</div>
                          <div className="text-sm text-gray-400">${c.menu_item.price.toFixed(2)} each</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => removeFromCart(c.menu_item.id)}
                            className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500"
                          >
                            -
                          </button>
                          <span className="w-6 text-center font-bold">{c.quantity}</span>
                          <button
                            onClick={() => addToCart(c.menu_item)}
                            className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center hover:bg-gray-500"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-gray-700 bg-gray-800">
                <div className="space-y-1 mb-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Subtotal</span>
                    <span>${cartSubtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tax (8.75%)</span>
                    <span>${cartTax.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold pt-2 border-t border-gray-600">
                    <span>Total</span>
                    <span className="text-truck-yellow">${cartTotal.toFixed(2)}</span>
                  </div>
                </div>
                <button
                  onClick={submitOrder}
                  disabled={cart.length === 0 || loading}
                  className="w-full bg-truck-green hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-all active:scale-95"
                >
                  {loading ? 'Processing...' : 'Submit Order'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Orders View */}
        {view === 'orders' && (
          <div className="p-4 overflow-y-auto h-full">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {orders.map(order => (
                <div key={order.id} className="order-card">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="text-2xl font-bold">#{order.order_number}</div>
                      <div className="text-sm text-gray-400">
                        {order.customer_name || 'Walk-in'}
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase status-${order.status}`}>
                      {order.status}
                    </span>
                  </div>

                  <div className="space-y-1 mb-3 text-sm">
                    {order.items.map((item, idx) => (
                      <div key={idx} className="flex justify-between">
                        <span>{item.quantity}x {item.menu_item_name}</span>
                        <span>${item.subtotal.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between font-bold border-t border-gray-600 pt-2 mb-3">
                    <span>Total</span>
                    <span className="text-truck-yellow">${order.total.toFixed(2)}</span>
                  </div>

                  {/* Status actions */}
                  <div className="flex gap-2 flex-wrap">
                    {order.status === 'pending' && (
                      <button
                        onClick={() => updateOrderStatus(order.id, 'preparing')}
                        className="flex-1 bg-blue-500 hover:bg-blue-600 py-2 rounded-lg text-sm font-medium"
                      >
                        Start Prep
                      </button>
                    )}
                    {order.status === 'preparing' && (
                      <button
                        onClick={() => updateOrderStatus(order.id, 'ready')}
                        className="flex-1 bg-green-500 hover:bg-green-600 py-2 rounded-lg text-sm font-medium"
                      >
                        Ready!
                      </button>
                    )}
                    {order.status === 'ready' && !order.is_paid && (
                      <>
                        <button
                          onClick={() => processPayment(order.id, 'cash')}
                          className="flex-1 bg-truck-yellow hover:bg-yellow-500 text-gray-900 py-2 rounded-lg text-sm font-medium"
                        >
                          💵 Cash
                        </button>
                        <button
                          onClick={() => processPayment(order.id, 'card')}
                          className="flex-1 bg-purple-500 hover:bg-purple-600 py-2 rounded-lg text-sm font-medium"
                        >
                          💳 Card
                        </button>
                      </>
                    )}
                    {order.status === 'ready' && order.is_paid && (
                      <button
                        onClick={() => updateOrderStatus(order.id, 'completed')}
                        className="flex-1 bg-gray-500 hover:bg-gray-600 py-2 rounded-lg text-sm font-medium"
                      >
                        Complete
                      </button>
                    )}
                    {order.is_paid && (
                      <span className="text-green-400 text-sm flex items-center">✓ Paid</span>
                    )}
                  </div>
                </div>
              ))}
              {orders.length === 0 && (
                <div className="text-center text-gray-500 py-12 col-span-full">
                  No orders today
                </div>
              )}
            </div>
          </div>
        )}

        {/* Queue Display View */}
        {view === 'queue' && (
          <div className="p-8 h-full bg-gray-900">
            <h2 className="text-3xl font-bold text-center mb-8">🍽️ Order Status</h2>
            <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
              {/* Preparing */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-blue-400">🔥 Preparing</h3>
                <div className="space-y-3">
                  {queue.filter(q => q.status === 'preparing').map(q => (
                    <div key={q.order_number} className="bg-blue-900/50 border border-blue-500 rounded-xl p-4">
                      <div className="text-3xl font-bold">#{q.order_number}</div>
                      <div className="text-gray-300">{q.customer_name}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ready */}
              <div>
                <h3 className="text-xl font-bold mb-4 text-green-400">✅ Ready for Pickup!</h3>
                <div className="space-y-3">
                  {queue.filter(q => q.status === 'ready' || q.status === 'pending').map(q => (
                    <div
                      key={q.order_number}
                      className={`rounded-xl p-4 ${
                        q.status === 'ready'
                          ? 'bg-green-900/50 border border-green-500 animate-pulse'
                          : 'bg-gray-800 border border-gray-600'
                      }`}
                    >
                      <div className="text-3xl font-bold">#{q.order_number}</div>
                      <div className="text-gray-300">{q.customer_name}</div>
                      {q.status === 'pending' && (
                        <div className="text-sm text-yellow-400 mt-1">~{q.wait_time_minutes} min</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {queue.length === 0 && (
              <div className="text-center text-gray-500 py-12">
                No active orders
              </div>
            )}
          </div>
        )}

        {/* Sales View */}
        {view === 'sales' && dailySales && (
          <div className="p-4 overflow-y-auto h-full">
            <h2 className="text-2xl font-bold mb-6">📊 Daily Sales - {dailySales.date}</h2>
            
            <div className="grid gap-4 md:grid-cols-4 mb-8">
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">Total Orders</div>
                <div className="text-3xl font-bold">{dailySales.total_orders}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">Revenue</div>
                <div className="text-3xl font-bold text-truck-green">${dailySales.total_revenue.toFixed(2)}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">💵 Cash</div>
                <div className="text-2xl font-bold">${dailySales.cash_total.toFixed(2)}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">💳 Card</div>
                <div className="text-2xl font-bold">${dailySales.card_total.toFixed(2)}</div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-xl p-4">
              <h3 className="text-lg font-bold mb-4">🏆 Top Items</h3>
              <div className="space-y-2">
                {dailySales.top_items.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-700 last:border-0">
                    <span className="font-medium">{item.name}</span>
                    <div className="text-right">
                      <span className="text-gray-400 mr-4">{item.quantity} sold</span>
                      <span className="text-truck-green">${item.revenue.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Settings View */}
        {view === 'settings' && (
          <div className="p-4 overflow-y-auto h-full">
            <h2 className="text-2xl font-bold mb-6">⚙️ Menu Management</h2>
            
            <div className="space-y-3">
              {menu.map(item => (
                <div key={item.id} className="flex items-center justify-between bg-gray-800 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{item.emoji}</span>
                    <div>
                      <div className="font-medium">{item.name}</div>
                      <div className="text-sm text-gray-400">${item.price.toFixed(2)} • {item.category}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => toggleAvailability(item.id)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      item.is_available
                        ? 'bg-green-500 hover:bg-green-600'
                        : 'bg-red-500 hover:bg-red-600'
                    }`}
                  >
                    {item.is_available ? 'Available' : 'Sold Out'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-gray-800 border-t border-gray-700 px-2 py-2 flex justify-around">
        {[
          { id: 'pos', icon: '🛒', label: 'POS' },
          { id: 'orders', icon: '📋', label: 'Orders' },
          { id: 'queue', icon: '📺', label: 'Queue' },
          { id: 'sales', icon: '📊', label: 'Sales' },
          { id: 'settings', icon: '⚙️', label: 'Menu' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setView(tab.id as View)}
            className={`flex flex-col items-center py-2 px-4 rounded-lg transition-all ${
              view === tab.id
                ? 'bg-truck-orange text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs mt-1">{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default App
