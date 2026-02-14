import { useState, useEffect, useCallback, useRef } from 'react'

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

interface KitchenOrder {
  id: number
  order_number: number
  customer_name: string
  status: string
  elapsed_seconds: number
  items: { name: string; quantity: number; customizations: string }[]
}

interface Location {
  id: number
  name: string
  address: string
  latitude: number | null
  longitude: number | null
  is_active: boolean
  notes: string
}

interface Shift {
  id: number
  staff_name: string
  started_at: string
  ended_at: string | null
  is_active: boolean
  starting_cash: number
  ending_cash: number | null
  expected_cash: number | null
  total_orders: number
  total_revenue: number
  total_tips: number
  cash_sales: number
  card_sales: number
  cash_variance: number | null
}

interface DailySales {
  date: string
  total_orders: number
  total_revenue: number
  cash_total: number
  card_total: number
  total_tips: number
  top_items: { name: string; quantity: number; revenue: number }[]
  average_order_value: number
}

type View = 'pos' | 'orders' | 'queue' | 'kitchen' | 'sales' | 'settings' | 'locations' | 'shifts'

// Sound effects (using Web Audio API)
const playSound = (type: 'success' | 'alert' | 'ding') => {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    
    if (type === 'success') {
      osc.frequency.value = 880
      gain.gain.value = 0.1
    } else if (type === 'alert') {
      osc.frequency.value = 440
      gain.gain.value = 0.15
    } else {
      osc.frequency.value = 660
      gain.gain.value = 0.1
    }
    
    osc.start()
    osc.stop(ctx.currentTime + 0.15)
  } catch (e) {
    // Audio not available
  }
}

// Format elapsed time
const formatElapsed = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

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
  const [kitchenOrders, setKitchenOrders] = useState<KitchenOrder[]>([])
  const [dailySales, setDailySales] = useState<DailySales | null>(null)
  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState('')
  const [showPayment, setShowPayment] = useState<Order | null>(null)
  const [tip, setTip] = useState(0)
  const [cashTendered, setCashTendered] = useState('')
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  
  // Feedback state
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedbackType, setFeedbackType] = useState<"bug" | "feature">("bug")
  const [feedbackMessage, setFeedbackMessage] = useState("")
  const [feedbackEmail, setFeedbackEmail] = useState("")
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  
  // Location state
  const [locations, setLocations] = useState<Location[]>([])
  const [activeLocation, setActiveLocation] = useState<Location | null>(null)
  const [showAddLocation, setShowAddLocation] = useState(false)
  const [newLocationName, setNewLocationName] = useState('')
  const [newLocationAddress, setNewLocationAddress] = useState('')
  const [gettingGPS, setGettingGPS] = useState(false)
  
  // Shift state
  const [activeShift, setActiveShift] = useState<Shift | null>(null)
  const [recentShifts, setRecentShifts] = useState<Shift[]>([])
  const [showStartShift, setShowStartShift] = useState(false)
  const [showCloseShift, setShowCloseShift] = useState(false)
  const [staffName, setStaffName] = useState('')
  const [startingCash, setStartingCash] = useState('')
  const [endingCash, setEndingCash] = useState('')
  const [shiftNotes, setShiftNotes] = useState('')
  
  const prevReadyCountRef = useRef(0)

  // Online/offline detection
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

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
      
      // Check for new ready orders
      const readyCount = data.filter((o: Order) => o.status === 'ready').length
      if (readyCount > prevReadyCountRef.current && prevReadyCountRef.current > 0) {
        playSound('ding')
      }
      prevReadyCountRef.current = readyCount
      
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

  // Fetch kitchen orders
  const fetchKitchenOrders = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/kitchen/orders`)
      const data = await res.json()
      setKitchenOrders(data)
    } catch (err) {
      console.error('Failed to fetch kitchen orders:', err)
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

  // Fetch locations
  const fetchLocations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/locations`)
      const data = await res.json()
      setLocations(data)
      const active = data.find((l: Location) => l.is_active)
      setActiveLocation(active || null)
    } catch (err) {
      console.error('Failed to fetch locations:', err)
    }
  }, [])

  // Activate location
  const activateLocation = async (locationId: number) => {
    try {
      await fetch(`${API_BASE}/locations/${locationId}/activate`, { method: 'POST' })
      fetchLocations()
      showNotification('Location activated!')
    } catch (err) {
      showNotification('Failed to activate location', 'alert')
    }
  }

  // Create location with optional GPS
  const createLocation = async (withGPS: boolean = false) => {
    if (!newLocationName.trim()) return
    
    let lat = null, lng = null
    
    if (withGPS && navigator.geolocation) {
      setGettingGPS(true)
      try {
        const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true })
        })
        lat = pos.coords.latitude
        lng = pos.coords.longitude
      } catch (err) {
        console.error('GPS failed:', err)
      }
      setGettingGPS(false)
    }
    
    try {
      await fetch(`${API_BASE}/locations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newLocationName.trim(),
          address: newLocationAddress.trim(),
          latitude: lat,
          longitude: lng
        })
      })
      setShowAddLocation(false)
      setNewLocationName('')
      setNewLocationAddress('')
      fetchLocations()
      showNotification('Location added!')
    } catch (err) {
      showNotification('Failed to add location', 'alert')
    }
  }

  // Delete location
  const deleteLocation = async (locationId: number) => {
    try {
      await fetch(`${API_BASE}/locations/${locationId}`, { method: 'DELETE' })
      fetchLocations()
      showNotification('Location deleted')
    } catch (err) {
      showNotification('Failed to delete location', 'alert')
    }
  }

  // Fetch shifts
  const fetchShifts = useCallback(async () => {
    try {
      const [activeRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/shifts/active`),
        fetch(`${API_BASE}/shifts?limit=10`)
      ])
      
      if (activeRes.ok) {
        const active = await activeRes.json()
        setActiveShift(active)
      } else {
        setActiveShift(null)
      }
      
      if (historyRes.ok) {
        const shifts = await historyRes.json()
        setRecentShifts(shifts)
      }
    } catch (err) {
      console.error('Failed to fetch shifts:', err)
    }
  }, [])

  // Start shift
  const startShift = async () => {
    if (!staffName.trim()) return
    
    try {
      await fetch(`${API_BASE}/shifts/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          staff_name: staffName.trim(),
          starting_cash: parseFloat(startingCash) || 0
        })
      })
      setShowStartShift(false)
      setStaffName('')
      setStartingCash('')
      fetchShifts()
      showNotification('Shift started!')
    } catch (err) {
      showNotification('Failed to start shift', 'alert')
    }
  }

  // Close shift
  const closeShift = async () => {
    if (!endingCash.trim()) return
    
    try {
      await fetch(`${API_BASE}/shifts/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ending_cash: parseFloat(endingCash) || 0,
          notes: shiftNotes.trim()
        })
      })
      setShowCloseShift(false)
      setEndingCash('')
      setShiftNotes('')
      fetchShifts()
      showNotification('Shift closed!')
    } catch (err) {
      showNotification('Failed to close shift', 'alert')
    }
  }

  // Initial load and polling
  useEffect(() => {
    fetchMenu()
    fetchOrders()
    fetchQueue()
    fetchLocations()
    fetchShifts()
    
    const interval = setInterval(() => {
      fetchOrders()
      fetchQueue()
      if (view === 'kitchen') {
        fetchKitchenOrders()
      }
    }, 3000)
    
    return () => clearInterval(interval)
  }, [fetchMenu, fetchOrders, fetchQueue, fetchKitchenOrders, fetchLocations, fetchShifts, view])

  useEffect(() => {
    if (view === 'sales') {
      fetchDailySales()
    }
    if (view === 'kitchen') {
      fetchKitchenOrders()
    }
    if (view === 'locations') {
      fetchLocations()
    }
    if (view === 'shifts') {
      fetchShifts()
    }
  }, [view, fetchDailySales, fetchKitchenOrders, fetchLocations, fetchShifts])

  // Show notification
  const showNotification = (msg: string, type: 'success' | 'alert' = 'success') => {
    setNotification(msg)
    playSound(type)
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
    playSound('success')
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

  // Quick combos
  const addCombo = (name: string, itemIds: number[]) => {
    const items = menu.filter(m => itemIds.includes(m.id) && m.is_available)
    items.forEach(item => addToCart(item))
    if (items.length > 0) {
      showNotification(`${name} added!`)
    }
  }

  // Calculate cart total
  const cartSubtotal = cart.reduce((sum, c) => sum + c.menu_item.price * c.quantity, 0)
  const cartTax = cartSubtotal * 0.0875
  const cartTotal = cartSubtotal + cartTax

  // Submit order
  const submitOrder = async (payNow: boolean = false) => {
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
        
        // If pay now, open payment modal
        if (payNow) {
          setShowPayment(order)
        }
      }
    } catch (err) {
      showNotification('Failed to create order', 'alert')
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
      fetchKitchenOrders()
    } catch (err) {
      console.error('Failed to update status:', err)
    }
  }

  // Kitchen bump
  const bumpOrder = async (orderId: number) => {
    try {
      await fetch(`${API_BASE}/kitchen/bump/${orderId}`, { method: 'POST' })
      fetchKitchenOrders()
      fetchOrders()
      playSound('success')
    } catch (err) {
      console.error('Failed to bump order:', err)
    }
  }

  // Process payment
  const processPayment = async (orderId: number, method: 'cash' | 'card') => {
    const order = orders.find(o => o.id === orderId)
    if (!order) return
    
    const totalWithTip = order.total + tip
    const cash = method === 'cash' && cashTendered ? parseFloat(cashTendered) : totalWithTip
    
    try {
      await fetch(`${API_BASE}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          amount: order.total,
          method,
          tip,
          cash_tendered: method === 'cash' ? cash : null
        })
      })
      
      const change = method === 'cash' ? cash - totalWithTip : 0
      showNotification(change > 0 ? `Payment received! Change: $${change.toFixed(2)}` : 'Payment received!')
      setShowPayment(null)
      setTip(0)
      setCashTendered('')
      fetchOrders()
    } catch (err) {
      showNotification('Payment failed', 'alert')
    }
  }

  // Submit feedback
  const submitFeedback = async () => {
    if (!feedbackMessage.trim()) return
    setSubmittingFeedback(true)
    try {
      await fetch(`${API_BASE}/feedback/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: feedbackType,
          message: feedbackMessage.trim(),
          email: feedbackEmail.trim() || null
        })
      })
      setFeedbackSubmitted(true)
      setTimeout(() => {
        setShowFeedbackModal(false)
        setFeedbackSubmitted(false)
        setFeedbackMessage("")
        setFeedbackEmail("")
      }, 2000)
    } catch (e) {
      console.error("Feedback submission failed:", e)
    }
    setSubmittingFeedback(false)
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
  
  // Pending orders count for badge
  const pendingCount = orders.filter(o => o.status === 'pending' || o.status === 'preparing').length

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 px-4 py-3 flex items-center justify-between border-b border-gray-700">
        <h1 className="text-xl font-bold flex items-center gap-2">
          🌮 Food Truck POS
        </h1>
        <div className="flex items-center gap-3">
          {activeLocation && (
            <button
              onClick={() => setView('locations')}
              className="text-xs bg-truck-orange/20 text-truck-orange px-2 py-1 rounded flex items-center gap-1 hover:bg-truck-orange/30"
            >
              📍 {activeLocation.name}
            </button>
          )}
          {!isOnline && (
            <span className="text-xs bg-yellow-500 text-yellow-900 px-2 py-1 rounded">OFFLINE</span>
          )}
          <div className="text-sm text-gray-400">
            {new Date().toLocaleDateString()}
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className="fixed top-16 left-1/2 -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-pulse">
          {notification}
        </div>
      )}

      {/* Floating Feedback Button */}
      <button
        onClick={() => setShowFeedbackModal(true)}
        className="fixed bottom-24 right-4 w-14 h-14 bg-truck-orange hover:bg-orange-600 rounded-full shadow-lg flex items-center justify-center text-2xl z-40 transition-transform hover:scale-110"
        title="Send Feedback"
      >
        💬
      </button>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl shadow-2xl p-6 max-w-lg w-full">
            {feedbackSubmitted ? (
              <div className="text-center py-8">
                <div className="text-5xl mb-4">✅</div>
                <h2 className="text-2xl font-bold text-green-400">Thank you!</h2>
                <p className="text-gray-400 mt-2">Your feedback has been submitted.</p>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-bold">Send Feedback</h2>
                  <button onClick={() => setShowFeedbackModal(false)} className="text-gray-400 hover:text-white text-2xl">&times;</button>
                </div>
                
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setFeedbackType("bug")}
                    className={`flex-1 py-3 rounded-lg font-semibold transition ${
                      feedbackType === "bug" ? "bg-red-600 text-white" : "bg-gray-700 hover:bg-gray-600"
                    }`}
                  >
                    🐛 Bug Report
                  </button>
                  <button
                    onClick={() => setFeedbackType("feature")}
                    className={`flex-1 py-3 rounded-lg font-semibold transition ${
                      feedbackType === "feature" ? "bg-truck-orange text-white" : "bg-gray-700 hover:bg-gray-600"
                    }`}
                  >
                    💡 Feature Request
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-1">
                      {feedbackType === "bug" ? "What went wrong?" : "What would you like?"}
                    </label>
                    <textarea
                      placeholder={feedbackType === "bug" 
                        ? "Describe the issue..."
                        : "Describe the feature..."}
                      value={feedbackMessage}
                      onChange={e => setFeedbackMessage(e.target.value)}
                      rows={4}
                      className="w-full p-3 bg-gray-700 border-2 border-gray-600 rounded-lg focus:border-truck-orange focus:outline-none resize-none text-white placeholder-gray-400"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-1">Email (optional)</label>
                    <input
                      type="email"
                      placeholder="your@email.com"
                      value={feedbackEmail}
                      onChange={e => setFeedbackEmail(e.target.value)}
                      className="w-full p-3 bg-gray-700 border-2 border-gray-600 rounded-lg focus:border-truck-orange focus:outline-none text-white placeholder-gray-400"
                    />
                  </div>
                </div>
                
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowFeedbackModal(false)}
                    className="flex-1 py-3 bg-gray-700 rounded-lg font-semibold hover:bg-gray-600"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitFeedback}
                    disabled={submittingFeedback || !feedbackMessage.trim()}
                    className="flex-1 py-3 bg-truck-orange text-white rounded-lg font-semibold hover:bg-orange-600 disabled:bg-gray-600 disabled:cursor-not-allowed"
                  >
                    {submittingFeedback ? "Sending..." : "Submit"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Payment - Order #{showPayment.order_number}</h2>
            
            <div className="space-y-3 mb-6">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>${(showPayment.total - showPayment.tax).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax</span>
                <span>${showPayment.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-lg font-bold">
                <span>Order Total</span>
                <span>${showPayment.total.toFixed(2)}</span>
              </div>
            </div>

            {/* Tip selection */}
            <div className="mb-4">
              <label className="text-sm text-gray-400 block mb-2">Add Tip</label>
              <div className="flex gap-2">
                {[0, 1, 2, 3, 5].map(t => (
                  <button
                    key={t}
                    onClick={() => setTip(t)}
                    className={`flex-1 py-2 rounded-lg font-medium ${
                      tip === t ? 'bg-truck-yellow text-gray-900' : 'bg-gray-700'
                    }`}
                  >
                    {t === 0 ? 'No Tip' : `$${t}`}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-between text-xl font-bold mb-6 pt-4 border-t border-gray-600">
              <span>Total with Tip</span>
              <span className="text-truck-green">${(showPayment.total + tip).toFixed(2)}</span>
            </div>

            {/* Cash tendered input */}
            <div className="mb-4">
              <label className="text-sm text-gray-400 block mb-2">Cash Tendered (optional)</label>
              <input
                type="number"
                value={cashTendered}
                onChange={e => setCashTendered(e.target.value)}
                placeholder="Enter amount..."
                className="w-full bg-gray-700 rounded-lg px-4 py-3 text-xl"
              />
              {cashTendered && parseFloat(cashTendered) >= showPayment.total + tip && (
                <div className="text-truck-green mt-2">
                  Change: ${(parseFloat(cashTendered) - showPayment.total - tip).toFixed(2)}
                </div>
              )}
            </div>

            {/* Quick cash buttons */}
            <div className="grid grid-cols-4 gap-2 mb-6">
              {[5, 10, 20, 50].map(amount => (
                <button
                  key={amount}
                  onClick={() => setCashTendered(amount.toString())}
                  className="bg-gray-700 hover:bg-gray-600 py-2 rounded-lg"
                >
                  ${amount}
                </button>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => processPayment(showPayment.id, 'cash')}
                className="flex-1 bg-truck-yellow hover:bg-yellow-500 text-gray-900 font-bold py-4 rounded-xl"
              >
                💵 Cash
              </button>
              <button
                onClick={() => processPayment(showPayment.id, 'card')}
                className="flex-1 bg-purple-500 hover:bg-purple-600 font-bold py-4 rounded-xl"
              >
                💳 Card
              </button>
            </div>

            <button
              onClick={() => { setShowPayment(null); setTip(0); setCashTendered(''); }}
              className="w-full mt-3 text-gray-400 py-2"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {/* POS View */}
        {view === 'pos' && (
          <div className="h-full flex flex-col lg:flex-row">
            {/* Menu Section */}
            <div className="flex-1 flex flex-col p-4 overflow-hidden">
              {/* Quick Combos */}
              <div className="flex gap-2 mb-3 overflow-x-auto no-scrollbar pb-2">
                <button
                  onClick={() => addCombo('Taco Combo', [1, 2, 14])}
                  className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 rounded-full whitespace-nowrap font-medium"
                >
                  🔥 Taco Combo
                </button>
                <button
                  onClick={() => addCombo('Burrito Special', [7, 10, 14])}
                  className="px-4 py-2 bg-gradient-to-r from-green-500 to-teal-500 rounded-full whitespace-nowrap font-medium"
                >
                  💪 Burrito Special
                </button>
              </div>

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
                <div className="flex gap-2">
                  <button
                    onClick={() => submitOrder(false)}
                    disabled={cart.length === 0 || loading}
                    className="flex-1 bg-truck-green hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl transition-all active:scale-95"
                  >
                    {loading ? '...' : 'Order'}
                  </button>
                  <button
                    onClick={() => submitOrder(true)}
                    disabled={cart.length === 0 || loading}
                    className="flex-1 bg-truck-yellow hover:bg-yellow-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 font-bold py-4 rounded-xl transition-all active:scale-95"
                  >
                    {loading ? '...' : '💰 Pay Now'}
                  </button>
                </div>
                {cart.length > 0 && (
                  <button
                    onClick={() => setCart([])}
                    className="w-full mt-2 text-red-400 text-sm py-2 hover:text-red-300"
                  >
                    Clear Cart
                  </button>
                )}
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
                      <button
                        onClick={() => setShowPayment(order)}
                        className="flex-1 bg-truck-yellow hover:bg-yellow-500 text-gray-900 py-2 rounded-lg text-sm font-medium"
                      >
                        💰 Pay
                      </button>
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

        {/* Kitchen Display View */}
        {view === 'kitchen' && (
          <div className="p-4 h-full bg-gray-900">
            <h2 className="text-2xl font-bold mb-6">👨‍🍳 Kitchen Display</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {kitchenOrders.map(order => (
                <div
                  key={order.id}
                  onClick={() => bumpOrder(order.id)}
                  className={`cursor-pointer rounded-xl p-4 transition-all hover:scale-105 ${
                    order.status === 'pending'
                      ? 'bg-yellow-900/50 border-2 border-yellow-500'
                      : 'bg-blue-900/50 border-2 border-blue-500'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="text-3xl font-bold">#{order.order_number}</div>
                    <div className={`text-lg font-mono ${
                      order.elapsed_seconds > 300 ? 'text-red-400' : 
                      order.elapsed_seconds > 180 ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {formatElapsed(order.elapsed_seconds)}
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-300 mb-3">{order.customer_name}</div>
                  
                  <div className="space-y-2">
                    {order.items.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2">
                        <span className="bg-gray-700 px-2 py-0.5 rounded text-sm font-bold">
                          {item.quantity}x
                        </span>
                        <span className="font-medium">{item.name}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className={`mt-4 text-center py-2 rounded-lg text-sm font-bold uppercase ${
                    order.status === 'pending' ? 'bg-yellow-500 text-yellow-900' : 'bg-blue-500'
                  }`}>
                    {order.status === 'pending' ? 'TAP TO START' : 'TAP WHEN DONE'}
                  </div>
                </div>
              ))}
              {kitchenOrders.length === 0 && (
                <div className="text-center text-gray-500 py-12 col-span-full text-xl">
                  🎉 All caught up!
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sales View */}
        {view === 'sales' && dailySales && (
          <div className="p-4 overflow-y-auto h-full">
            <h2 className="text-2xl font-bold mb-6">📊 Daily Sales - {dailySales.date}</h2>
            
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
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

            <div className="grid gap-4 md:grid-cols-2 mb-8">
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">💰 Tips Collected</div>
                <div className="text-2xl font-bold text-truck-yellow">${dailySales.total_tips.toFixed(2)}</div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="text-gray-400 text-sm">📈 Avg Order Value</div>
                <div className="text-2xl font-bold">${dailySales.average_order_value.toFixed(2)}</div>
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

        {/* Locations View */}
        {view === 'locations' && (
          <div className="p-4 overflow-y-auto h-full">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">📍 Locations & Events</h2>
              <button
                onClick={() => setShowAddLocation(true)}
                className="bg-truck-orange hover:bg-orange-600 px-4 py-2 rounded-lg font-medium"
              >
                + Add Location
              </button>
            </div>

            {/* Add Location Modal */}
            {showAddLocation && (
              <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
                  <h3 className="text-xl font-bold mb-4">Add New Location</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Location Name</label>
                      <input
                        type="text"
                        value={newLocationName}
                        onChange={e => setNewLocationName(e.target.value)}
                        placeholder="e.g., Downtown Farmers Market"
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Address (optional)</label>
                      <input
                        type="text"
                        value={newLocationAddress}
                        onChange={e => setNewLocationAddress(e.target.value)}
                        placeholder="123 Main St"
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange"
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={() => { setShowAddLocation(false); setNewLocationName(''); setNewLocationAddress(''); }}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => createLocation(false)}
                      disabled={!newLocationName.trim()}
                      className="flex-1 bg-gray-600 hover:bg-gray-500 py-3 rounded-lg disabled:opacity-50"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => createLocation(true)}
                      disabled={!newLocationName.trim() || gettingGPS}
                      className="flex-1 bg-truck-orange hover:bg-orange-600 py-3 rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {gettingGPS ? '📡...' : '📍 + GPS'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Current Location */}
            {activeLocation && (
              <div className="bg-truck-orange/20 border-2 border-truck-orange rounded-xl p-4 mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">📍</span>
                  <span className="text-lg font-bold">Currently At:</span>
                </div>
                <div className="text-2xl font-bold">{activeLocation.name}</div>
                {activeLocation.address && (
                  <div className="text-gray-300">{activeLocation.address}</div>
                )}
                {activeLocation.latitude && (
                  <div className="text-sm text-gray-400 mt-1">
                    GPS: {activeLocation.latitude.toFixed(4)}, {activeLocation.longitude?.toFixed(4)}
                  </div>
                )}
              </div>
            )}

            {/* Saved Locations */}
            <h3 className="text-lg font-bold mb-3">Saved Locations</h3>
            <div className="space-y-3">
              {locations.map(loc => (
                <div
                  key={loc.id}
                  className={`flex items-center justify-between rounded-xl p-4 ${
                    loc.is_active ? 'bg-truck-orange/10 border border-truck-orange' : 'bg-gray-800'
                  }`}
                >
                  <div className="flex-1">
                    <div className="font-medium flex items-center gap-2">
                      {loc.name}
                      {loc.is_active && <span className="text-xs bg-truck-orange text-white px-2 py-0.5 rounded">ACTIVE</span>}
                    </div>
                    {loc.address && <div className="text-sm text-gray-400">{loc.address}</div>}
                    {loc.latitude && (
                      <div className="text-xs text-gray-500">GPS: {loc.latitude.toFixed(4)}, {loc.longitude?.toFixed(4)}</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {!loc.is_active && (
                      <button
                        onClick={() => activateLocation(loc.id)}
                        className="bg-truck-green hover:bg-green-600 px-4 py-2 rounded-lg text-sm font-medium"
                      >
                        Check In
                      </button>
                    )}
                    <button
                      onClick={() => deleteLocation(loc.id)}
                      className="bg-red-500/20 hover:bg-red-500/30 text-red-400 px-3 py-2 rounded-lg text-sm"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
              {locations.length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  No locations saved yet. Add your first spot!
                </div>
              )}
            </div>

            {/* Tips */}
            <div className="mt-8 bg-gray-800 rounded-xl p-4">
              <h4 className="font-bold mb-2">💡 Pro Tips</h4>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• Check in when you arrive to track sales by location</li>
                <li>• Use GPS to save exact coordinates for events</li>
                <li>• Review location sales in the Sales report</li>
              </ul>
            </div>
          </div>
        )}

        {/* Shifts View */}
        {view === 'shifts' && (
          <div className="p-4 overflow-y-auto h-full">
            <h2 className="text-2xl font-bold mb-6">⏱️ Shift Management</h2>

            {/* Start Shift Modal */}
            {showStartShift && (
              <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
                  <h3 className="text-xl font-bold mb-4">Start New Shift</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Staff Name</label>
                      <input
                        type="text"
                        value={staffName}
                        onChange={e => setStaffName(e.target.value)}
                        placeholder="Your name"
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Starting Drawer Cash</label>
                      <input
                        type="number"
                        value={startingCash}
                        onChange={e => setStartingCash(e.target.value)}
                        placeholder="0.00"
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange"
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={() => { setShowStartShift(false); setStaffName(''); setStartingCash(''); }}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={startShift}
                      disabled={!staffName.trim()}
                      className="flex-1 bg-truck-green hover:bg-green-600 py-3 rounded-lg disabled:opacity-50"
                    >
                      Start Shift
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Close Shift Modal */}
            {showCloseShift && activeShift && (
              <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
                  <h3 className="text-xl font-bold mb-4">Close Shift</h3>
                  
                  <div className="bg-gray-700 rounded-lg p-4 mb-4">
                    <div className="text-sm text-gray-400 mb-2">Shift Summary</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Orders: <span className="font-bold">{activeShift.total_orders}</span></div>
                      <div>Revenue: <span className="font-bold text-truck-green">${activeShift.total_revenue.toFixed(2)}</span></div>
                      <div>Cash Sales: <span className="font-bold">${activeShift.cash_sales.toFixed(2)}</span></div>
                      <div>Tips: <span className="font-bold text-truck-yellow">${activeShift.total_tips.toFixed(2)}</span></div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-600">
                      <div className="text-lg font-bold">
                        Expected Cash: ${((activeShift.starting_cash || 0) + (activeShift.cash_sales || 0)).toFixed(2)}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Actual Drawer Cash</label>
                      <input
                        type="number"
                        value={endingCash}
                        onChange={e => setEndingCash(e.target.value)}
                        placeholder="Count your drawer..."
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange text-xl"
                      />
                      {endingCash && (
                        <div className={`mt-2 text-lg font-bold ${
                          parseFloat(endingCash) >= (activeShift.starting_cash + activeShift.cash_sales) ? 'text-green-400' : 'text-red-400'
                        }`}>
                          Variance: ${(parseFloat(endingCash) - (activeShift.starting_cash + activeShift.cash_sales)).toFixed(2)}
                        </div>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Notes (optional)</label>
                      <textarea
                        value={shiftNotes}
                        onChange={e => setShiftNotes(e.target.value)}
                        placeholder="Any notes about the shift..."
                        rows={2}
                        className="w-full bg-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-truck-orange resize-none"
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={() => { setShowCloseShift(false); setEndingCash(''); setShiftNotes(''); }}
                      className="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={closeShift}
                      disabled={!endingCash.trim()}
                      className="flex-1 bg-red-500 hover:bg-red-600 py-3 rounded-lg disabled:opacity-50"
                    >
                      Close Shift
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Active Shift Card */}
            {activeShift ? (
              <div className="bg-truck-green/20 border-2 border-truck-green rounded-xl p-4 mb-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="text-sm text-gray-400">Active Shift</div>
                    <div className="text-2xl font-bold">{activeShift.staff_name}</div>
                    <div className="text-sm text-gray-400">
                      Started: {new Date(activeShift.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                  <span className="bg-truck-green text-white px-3 py-1 rounded-full text-sm font-bold animate-pulse">
                    🟢 ACTIVE
                  </span>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-400">Orders</div>
                    <div className="text-xl font-bold">{activeShift.total_orders}</div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-400">Revenue</div>
                    <div className="text-xl font-bold text-truck-green">${activeShift.total_revenue.toFixed(2)}</div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-400">Cash Sales</div>
                    <div className="text-xl font-bold">${activeShift.cash_sales.toFixed(2)}</div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-400">Tips</div>
                    <div className="text-xl font-bold text-truck-yellow">${activeShift.total_tips.toFixed(2)}</div>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowCloseShift(true)}
                  className="w-full bg-red-500 hover:bg-red-600 py-3 rounded-lg font-bold"
                >
                  Close Shift
                </button>
              </div>
            ) : (
              <div className="bg-gray-800 rounded-xl p-6 mb-6 text-center">
                <div className="text-4xl mb-4">⏰</div>
                <div className="text-xl font-bold mb-2">No Active Shift</div>
                <p className="text-gray-400 mb-4">Start a shift to track sales and manage the cash drawer.</p>
                <button
                  onClick={() => setShowStartShift(true)}
                  className="bg-truck-green hover:bg-green-600 px-8 py-3 rounded-lg font-bold"
                >
                  Start Shift
                </button>
              </div>
            )}

            {/* Recent Shifts History */}
            <h3 className="text-lg font-bold mb-3">Recent Shifts</h3>
            <div className="space-y-3">
              {recentShifts.filter(s => !s.is_active).map(shift => (
                <div key={shift.id} className="bg-gray-800 rounded-xl p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-bold">{shift.staff_name}</div>
                      <div className="text-sm text-gray-400">
                        {new Date(shift.started_at).toLocaleDateString()} • {new Date(shift.started_at).toLocaleTimeString()} - {shift.ended_at ? new Date(shift.ended_at).toLocaleTimeString() : 'N/A'}
                      </div>
                    </div>
                    {shift.cash_variance !== null && (
                      <span className={`text-sm font-bold ${shift.cash_variance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {shift.cash_variance >= 0 ? '+' : ''}${shift.cash_variance.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-sm">
                    <div>
                      <div className="text-gray-500">Orders</div>
                      <div className="font-bold">{shift.total_orders}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Revenue</div>
                      <div className="font-bold text-truck-green">${shift.total_revenue.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Cash</div>
                      <div className="font-bold">${shift.cash_sales.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Tips</div>
                      <div className="font-bold text-truck-yellow">${shift.total_tips.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))}
              {recentShifts.filter(s => !s.is_active).length === 0 && (
                <div className="text-center text-gray-500 py-8">
                  No shift history yet
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-gray-800 border-t border-gray-700 px-2 py-2 flex justify-around">
        {[
          { id: 'pos', icon: '🛒', label: 'POS' },
          { id: 'orders', icon: '📋', label: 'Orders', badge: pendingCount },
          { id: 'kitchen', icon: '👨‍🍳', label: 'Kitchen' },
          { id: 'queue', icon: '📺', label: 'Queue' },
          { id: 'sales', icon: '📊', label: 'Sales' },
          { id: 'shifts', icon: '⏱️', label: 'Shift' },
          { id: 'locations', icon: '📍', label: 'Location' },
          { id: 'settings', icon: '⚙️', label: 'Menu' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setView(tab.id as View)}
            className={`relative flex flex-col items-center py-2 px-3 rounded-lg transition-all ${
              view === tab.id
                ? 'bg-truck-orange text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs mt-1">{tab.label}</span>
            {tab.badge && tab.badge > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  )
}

export default App
