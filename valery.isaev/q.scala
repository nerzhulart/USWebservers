import scala.util.control.Breaks._
import scala.collection.immutable.{Map,StringOps}
import java.lang.{Process,ProcessBuilder}
import java.io.{FileWriter,File,FileInputStream}
import java.text.{SimpleDateFormat,ParseException}
import java.util.{Date,Locale,Calendar}

val socket = new java.net.ServerSocket(1234)
val log = new FileWriter("q.log", true)
val getReq = "GET (?:http://.*)?/(.*) HTTP/1\\..".r
val fileExt = ".*\\.([^/]*)".r
val responses = Map (
    200 -> "HTTP/1.1 200/OK"
  , 304 -> "HTTP/1.1 304/Not Modified"
  , 400 -> "HTTP/1.1 400/Bad Request"
  , 404 -> "HTTP/1.1 404/Not Found"
  , 500 -> "HTTP/1.1 500/Internal Server Error"
  )
val mimes = Map (
    "html"  -> "text/html"
  , "txt"   -> "text/plain"
  , "xml"   -> "text/xml"
  , "jpg"   -> "image/jpeg"
  , "png"   -> "image/png"
  , "gif"   -> "image/gif"
  , "mp3"   -> "audio/mpeg"
  , "zip"   -> "application/zip"
  , "gz"    -> "application/x-gzip"
  , "pdf"   -> "application/pdf"
  , "avi"   -> "video/mpeg"
  , "scala" -> "text/html"
  )

while (true) {
    val client = socket.accept
    scala.concurrent.ops.spawn {
        val output = client.getOutputStream
        def answer(ans : Int, url : String = "") {
            output.write((responses(ans) ++ "\n").getBytes)
            log.append("[" + Calendar.getInstance.getTime.toString + "] " + client.getInetAddress.getHostAddress + " " + url + " " + ans + "\n")
            log.flush
        }
        try {
            val input = new scala.io.BufferedSource(client.getInputStream).getLines
            if (input.hasNext) {
                val request = input.next
                var date : Date = null
                breakable {
                    for (attr <- input) {
                        if (attr == "") break
                        val pair = new StringOps(attr).span(':' !=)
                        if (pair._1 == "If-Modified-Since") {
                            try {
                                date = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss z", Locale.US).parse(pair._2.drop(2))
                                break
                            } catch {
                                case _: ParseException => ;
                            }
                        }
                    }
                }
                request match {
                    case getReq(url) => {
                        val file = new File(url)
                        if (!file.exists) {
                            answer(404, url)
                            return
                        }
                        if (date != null && date.after(new Date(file.lastModified))) {
                            answer(304, url)
                            return
                        }
                        var isScript = false
                        var contentType = "\n"
                        for { ext <- fileExt.unapplySeq(url)
                              mime <- mimes.get(ext.head) } {
                            contentType = "Content-type: " + mime + "\n\n"
                            if (ext.head == "scala") {
                                isScript = true
                            }
                        }
                        if (isScript) {
                            val bs = new scala.io.BufferedSource(new ProcessBuilder("scala", url).start.getInputStream)
                            answer(200, url)
                            output.write(contentType.getBytes)
                            for (line <- bs.getLines) {
                                output.write((line + "\n").getBytes)
                            }
                        } else {
                            val is = new FileInputStream(file)
                            val b = new Array[Byte](4096)
                            answer(200, url)
                            output.write(contentType.getBytes)
                            var k = is.read(b)
                            while (k >= 0) {
                                output.write(b, 0, k)
                                k = is.read(b)
                            }
                        }
                    }
                    case _ => answer(400)
                }
            } else {
                answer(400)
            }
        } catch {
            case e => {
                answer(500)
                log.append("[" + Calendar.getInstance.getTime.toString + "] ERROR: " + e.toString + "\n")
                log.flush
            }
        }
        output.flush
        client.close
    }
}
