import proxy as proxy
import exporterlog

if __name__ == "__main__":
    exporterlog.ExporterLog.start()
    proxy.start()