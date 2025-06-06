import socket

def Has_IPv6_Addr(target_host="ipv6.google.com", target_port=80, timeout=5):
    """
    檢查此主機是否具有 IPv6 連線能力，透過嘗試建立實際的 TCP 連線到外部 IPv6 服務。

    Args:
        target_host (str): 要測試連線的目標主機名稱 (可以是 IPv6 位址或域名)。
                           預設為 Google 的 IPv6 服務。
        target_port (int): 目標服務的 Port，預設為 80 (HTTP)。
        timeout (int): 連線超時時間 (秒)。

    回傳:
        bool: 如果能透過 IPv6 成功建立 TCP 連線則回傳 True，否則回傳 False。
    """
    # 步驟 1: 快速檢查本機系統是否支援 IPv6
    # 這裡使用 socket.has_ipv6 確保本地 IPv6 堆疊正常
    if not socket.has_ipv6:
        return False

    try:
        # 嘗試綁定到 IPv6 loopback address，檢查本機 IPv6 堆疊是否正常
        # 這是為了確保 IPv6 基礎設施在本地是可用的
        sock_test_local = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock_test_local.bind(('::1', 0)) # 綁定到 IPv6 loopback address
        sock_test_local.close()
    except OSError:
        # 如果無法綁定，表示本機 IdPv6 環境有問題
        return False

    # 步驟 2: 嘗試建立一個實際的 IPv6 TCP 連線到外部服務
    sock_connect = None
    try:
        # 取得目標主機的 IPv6 位址資訊 (可能有多個，通常取第一個)
        # getaddrinfo 會處理 DNS 解析，並回傳適合的 socket family (AF_INET6)
        # 如果 target_host 沒有 IPv6 位址，這一步可能會拋出 socket.gaierror
        addr_info = socket.getaddrinfo(target_host, target_port,
                                        socket.AF_INET6, socket.SOCK_STREAM)
        if not addr_info:
            return False # 沒有找到可用的 IPv6 位址資訊

        # 取出第一個 IPv6 位址資訊
        af, socktype, proto, canonname, sa = addr_info[0]

        sock_connect = socket.socket(af, socktype, proto)
        sock_connect.settimeout(timeout) # 設定連線超時時間
        sock_connect.connect(sa) # 嘗試連線
        return True # 連線成功

    except socket.gaierror:
        # DNS 解析失敗，或者目標主機沒有 IPv6 位址
        return False
    except socket.timeout:
        # 連線超時
        return False
    except ConnectionRefusedError:
        # 連線被拒絕 (目標服務可能沒有運行或防火牆阻擋)
        return False
    except OSError as e:
        # 其他作業系統相關的網路錯誤
        # print(f"連線 IPv6 服務時發生作業系統錯誤: {e}")
        return False
    except Exception as e:
        # 捕獲其他所有可能的例外
        # print(f"連線 IPv6 服務時發生未知錯誤: {e}")
        return False
    finally:
        if sock_connect:
            sock_connect.close() # 確保 socket 被關閉