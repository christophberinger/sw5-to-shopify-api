import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { shopwareApi, shopifyApi } from '../utils/api'

function ConnectionStatus() {
  const [sw5Status, setSw5Status] = useState<{ connected: boolean; info?: any }>({
    connected: false,
  })
  const [shopifyStatus, setShopifyStatus] = useState<{ connected: boolean; info?: any }>({
    connected: false,
  })
  const [loading, setLoading] = useState(false)

  const testConnections = async () => {
    setLoading(true)

    try {
      const sw5Result = await shopwareApi.testConnection()
      setSw5Status({
        connected: sw5Result.success,
        info: sw5Result,
      })

      if (!sw5Result.success) {
        toast.error('Shopware 5 Verbindung fehlgeschlagen')
      }
    } catch (error) {
      setSw5Status({ connected: false })
      toast.error('Shopware 5 Verbindung fehlgeschlagen')
    }

    try {
      const shopifyResult = await shopifyApi.testConnection()
      setShopifyStatus({
        connected: shopifyResult.success,
        info: shopifyResult,
      })

      if (!shopifyResult.success) {
        toast.error('Shopify Verbindung fehlgeschlagen')
      }
    } catch (error) {
      setShopifyStatus({ connected: false })
      toast.error('Shopify Verbindung fehlgeschlagen')
    }

    setLoading(false)
  }

  useEffect(() => {
    testConnections()
  }, [])

  return (
    <div className="card">
      <h2>Verbindungsstatus</h2>

      <div className="connection-status">
        <div className="connection-item">
          <div
            className={`connection-indicator ${
              sw5Status.connected ? 'connected' : 'disconnected'
            }`}
          />
          <div>
            <strong>Shopware 5:</strong>{' '}
            {sw5Status.connected ? (
              <>
                Verbunden
                {sw5Status.info?.version && ` (v${sw5Status.info.version})`}
              </>
            ) : (
              'Nicht verbunden'
            )}
          </div>
        </div>

        <div className="connection-item">
          <div
            className={`connection-indicator ${
              shopifyStatus.connected ? 'connected' : 'disconnected'
            }`}
          />
          <div>
            <strong>Shopify:</strong>{' '}
            {shopifyStatus.connected ? (
              <>
                Verbunden
                {shopifyStatus.info?.shop_name && ` (${shopifyStatus.info.shop_name})`}
              </>
            ) : (
              'Nicht verbunden'
            )}
          </div>
        </div>
      </div>

      <button
        className="button button-secondary"
        onClick={testConnections}
        disabled={loading}
      >
        {loading ? 'Teste Verbindungen...' : 'Verbindungen testen'}
      </button>
    </div>
  )
}

export default ConnectionStatus
