/**
 * pywebview 桥接：获取 window.pywebview.api，支持 pywebviewready 异步就绪。
 * @returns {Promise<object>} api
 */
export function usePywebview() {
  const getApi = () => {
    if (typeof window !== 'undefined' && window.pywebview && window.pywebview.api) {
      return Promise.resolve(window.pywebview.api)
    }
    return new Promise((resolve) => {
      const onReady = () => resolve(window.pywebview?.api || null)
      if (typeof window !== 'undefined') {
        window.addEventListener('pywebviewready', onReady, { once: true })
        if (window.pywebview?.api) {
          window.removeEventListener('pywebviewready', onReady)
          resolve(window.pywebview.api)
        }
      } else {
        resolve(null)
      }
    })
  }
  return { getApi }
}
