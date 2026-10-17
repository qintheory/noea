import AVFoundation
import AppKit
let args = CommandLine.arguments
let dir = args[1], out = args[2], fps = Int32(args[3])!
let files = try! FileManager.default.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".png") }.sorted()
try? FileManager.default.removeItem(atPath: out)
let w = try! AVAssetWriter(url: URL(fileURLWithPath: out), fileType: .mp4)
let s = [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: 1920, AVVideoHeightKey: 1080,
         AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 8_000_000, AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel]] as [String: Any]
let inp = AVAssetWriterInput(mediaType: .video, outputSettings: s)
let ad = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: inp, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String: 1920, kCVPixelBufferHeightKey as String: 1080])
w.add(inp); w.startWriting(); w.startSession(atSourceTime: .zero)
for (i, f) in files.enumerated() {
    while !inp.isReadyForMoreMediaData { Thread.sleep(forTimeInterval: 0.005) }
    let img = NSImage(contentsOfFile: dir + "/" + f)!.cgImage(forProposedRect: nil, context: nil, hints: nil)!
    var pb: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(kCFAllocatorDefault, ad.pixelBufferPool!, &pb)
    CVPixelBufferLockBaseAddress(pb!, [])
    let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: 1920, height: 1080, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(pb!), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue)!
    ctx.draw(img, in: CGRect(x: 0, y: 0, width: 1920, height: 1080))
    CVPixelBufferUnlockBaseAddress(pb!, [])
    ad.append(pb!, withPresentationTime: CMTime(value: Int64(i), timescale: fps))
}
inp.markAsFinished()
let sem = DispatchSemaphore(value: 0)
w.finishWriting { sem.signal() }
sem.wait()
print(w.status == .completed ? "ok \(files.count) frames" : "failed \(String(describing: w.error))")
