# Codex → Chrome：接入与截图

## 接入

使用当前会话的 `cua_repl`／Browser Use 文档。第一次调用只做工具要求的初始化入口；用户给出标签引用时优先绑定它，否则按 URL 选择或在指定 Chrome 新建标签。给新浏览器任务起可识别的 session 名称。不要改用独立 Playwright 进程，也不要读取浏览器配置目录、Cookie 或会话数据库。

运行时会跨调用保留变量，复用已绑定的浏览器与标签。只有绑定失效或工具明确要求时才重新取得对象，不逐次 reset。工具缺失、未登录或页面无法访问时，说明具体阻塞；不改变账号或扩大权限来试通。

下面均为完成当前工具初始化、页面已加载之后的代码片段，变量 `browser`、`tab` 代表当前已绑定对象。实际工具版本的文档优先。`tab.playwright` 是已连接浏览器提供的 DOM 接口，不是另行启动的浏览器。

## 视口

为完整容纳指定清晰度的幻灯片，读取当前浏览器的 `viewport` capability 文档，再设置所需尺寸：

```js
const viewport = await browser.capabilities.get("viewport");
// 先阅读 await viewport.documentation()
await viewport.set({ width: 2560, height: 1440 });
// 截图工作结束或失败后均执行 await viewport.reset()
```

这只调整视口。飞书画布仍需在编辑器内单独缩放。留意 Chrome 页面缩放、设备像素倍率和编辑器画布缩放是不同参数。

## 坐标与编码

页面 `getBoundingClientRect()` 使用 CSS 视口坐标。真实截图可能按设备倍率输出，工具显示的预览还可能再次缩小。不能把聊天中的截图像素直接作为页面点击坐标。

按当前接口的坐标定义进行点击：若接口接收 CSS 页面坐标，使用本次目录项矩形计算；若接口接收截图坐标，使用本次截图与视口的映射。读完矩形后若发生滚动，应重新读取。DOM `evaluate` 若限于只读，不能在其中调用 `click()`、`scrollIntoView()` 或修改样式；改用工具提供的 UI 点击／滚动。

2026-10-15 在当前 Codex Chrome 连接中，用公开文档页做了局部截图验证：

- `tab.screenshot({ clip })` 返回 JPEG 字节（文件头 `FF D8 FF`）。
- 经该标签 `cdp` capability 调用 `Page.captureScreenshot` 并指定 `format: "png"`，返回 PNG 的 Base64。
- 当 `devicePixelRatio=2` 时，320×180 的区域、`scale=1` 输出 640×360 PNG；`scale=0.5` 输出 320×180 PNG。

这是当前环境的实测，不是所有版本的固定行为；首张样本仍需检查实际文件。

## 原生 PNG 截图

优先使用高层截图 API；它不能提供所需 PNG 时，只有当前工具确实暴露并允许 `cdp` capability 才使用以下路径。先阅读 capability 文档；标签必须已导航到实际 HTTP(S) 页面，不能在空白页直接发命令。不得用 CDP 扩大页面访问范围或绕过工具拒绝。

从当前已核实的画布读取矩形和设备倍率；此处 `canvasSelector` 来自现场页面确认：

```js
const capture = await tab.playwright.evaluate((selector) => {
  const nodes = document.querySelectorAll(selector);
  if (nodes.length !== 1) throw new Error("需要唯一的当前画布");
  const r = nodes[0].getBoundingClientRect();
  return {
    x: r.x, y: r.y, width: r.width, height: r.height,
    right: r.right, bottom: r.bottom,
    viewportWidth: innerWidth, viewportHeight: innerHeight,
    scrollX, scrollY, dpr: devicePixelRatio
  };
}, canvasSelector);
```

先验证画布四边未越界，再对四边取整得到 `left`、`top`、`right`、`bottom`；用 `right-left`、`bottom-top` 计算宽高，不静默缩边或裁掉正文。若目标为 1920×1080，取整后不满足该尺寸就先调整页面，不进入合成。

截图的页面坐标需考虑顶层滚动；飞书常见布局的顶层滚动为 0，但应现场读取，目录容器滚动不等于顶层滚动。

```js
const cdp = await tab.capabilities.get("cdp");
const result = await cdp.send("Page.captureScreenshot", {
  format: "png",
  captureBeyondViewport: false,
  clip: {
    x: left + capture.scrollX,
    y: top + capture.scrollY,
    width: right - left,
    height: bottom - top,
    scale: 1 / capture.dpr
  }
});
const bytes = Buffer.from(result.data, "base64");
```

`1 / dpr` 是当前验证过的起始校准方式，不能代替结果验收。PNG 文件头应为 `89 50 4E 47 0D 0A 1A 0A`；IHDR 宽高位于字节 16、20，各为 4 字节大端整数，或用 Pillow 解码检查。若当前倍率行为不同，根据样本实际尺寸与目标尺寸的比值重新校准；不对已截低清图片放大。

把字节通过当前运行时支持的本地文件 I/O 写入任务目录，输出元数据即可，不把 Base64 打到聊天。无原生 PNG 能力时可以保留真实 JPEG，再用合成脚本处理；JPEG 改存 PNG 不会恢复已丢失的信息。

接口参考：[Chrome DevTools Protocol — Page.captureScreenshot](https://chromedevtools.github.io/devtools-protocol/#/Page.captureScreenshot)。
