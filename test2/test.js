// 全局变量
let instance;
let eventLog = [];
const maxLogItems = 50;

// 初始化
function init() {
  const canvas = document.querySelector(".canvas");
  canvas.addEventListener("mousewheel", (e) => {
    console.log(e.wheelDelta);
    e.preventDefault();
  });
  instance = new CanvasSelect(
    canvas,
    document.getElementById("imageUrl").value
  );
  window.instance = instance;

  // 设置初始属性
  instance.ctrlRadius = navigator.userAgent.includes("Mobile") ? 6 : 3;
  instance.createType = 0;

  // 绑定事件监听
  setupEventListeners();

  // 更新UI状态
  updateUI();

  showToast("Canvas-Select 初始化完成！", "success");
}

// 设置事件监听
function setupEventListeners() {
  // 图片加载完成
  instance.on("load", (src) => {
    addEventLog("图片加载完成", { src });
    updateUI();
  });

  // 警告信息
  instance.on("warn", (msg) => {
    addEventLog("警告", { message: msg });
    showToast(msg, "warning");
  });

  // 添加标注
  instance.on("add", (info) => {
    addEventLog("添加标注", {
      type: getShapeTypeName(info.type),
      label: info.label || "无标签",
      uuid: info.uuid
    });
    updateUI();
  });

  // 删除标注
  instance.on("delete", (info) => {
    addEventLog("删除标注", {
      type: getShapeTypeName(info.type),
      label: info.label || "无标签",
      uuid: info.uuid
    });
    updateUI();
  });

  // 选中标注
  instance.on("select", (info) => {
    if (info) {
      addEventLog("选中标注", {
        type: getShapeTypeName(info.type),
        label: info.label || "无标签",
        uuid: info.uuid
      });
    } else {
      addEventLog("取消选中", {});
    }
    updateUI();
  });

  // 数据更新
  instance.on("updated", (result) => {
    updateDataOutput(result);
    updateShapeCount(result.length);
    updateScaleInfo();
  });

  // 右键菜单
  instance.on("contextmenu", (e) => {
    addEventLog("右键", instance.mouse);
  });

  instance.on("coor", (s) => {
    console.log("coor", s);
  });

  // 监听鼠标移动显示坐标
  const canvas = document.querySelector(".canvas");
  canvas.addEventListener("mousemove", (e) => {
    document.getElementById(
      "mousePos"
    ).textContent = `${instance.mouse[0]}, ${instance.mouse[0]}`;
    document.getElementById(
      "mousePos2"
    ).textContent = `${instance.position[0]}, ${instance.position[1]}`;
  });
}

// 设置创建类型
function setCreateType(type) {
  instance.createType = type;

  // 更新按钮状态
  document.querySelectorAll('.btn[id^="btn-"]').forEach((btn) => {
    btn.classList.remove("active");
  });
  document.getElementById(`btn-${type}`).classList.add("active");

  // 更新当前模式显示
  const modeNames = {
    0: "选择模式",
    1: "矩形",
    2: "多边形",
    3: "点标注",
    4: "折线",
    5: "圆形",
    6: "网格",
    7: "画笔",
    8: "橡皮擦"
  };
  document.getElementById("currentMode").textContent = modeNames[type];

  addEventLog("切换创建模式", { mode: modeNames[type] });
}

// 缩放控制
function zoomIn() {
  instance.setScale(true);
  addEventLog("放大画布", {});
}

function zoomOut() {
  instance.setScale(false);
  addEventLog("缩小画布", {});
}

function fitZoom() {
  instance.fitZoom();
  addEventLog("适配画布", {});
}

function toggleFocusMode() {
  instance.setFocusMode(!instance.focusMode);
  addEventLog("切换专注模式", { enabled: instance.focusMode });
  updateUI();
}

// 切换功能
function toggleCross() {
  instance.showCross = document.getElementById("showCross").checked;
  instance.update();
  addEventLog("切换十字坐标线", { enabled: instance.showCross });
}

function toggleScrollZoom() {
  instance.scrollZoom = document.getElementById("scrollZoom").checked;
  addEventLog("切换滚轮缩放", { enabled: instance.scrollZoom });
}

function toggleReadonly() {
  instance.readonly = document.getElementById("readonly").checked;
  addEventLog("切换只读模式", { enabled: instance.readonly });
}

function toggleLock() {
  instance.lock = document.getElementById("lock").checked;
  addEventLog("切换锁定模式", { enabled: instance.lock });
}

function toggleShowRotation() {
  instance.showRotation = document.getElementById("showRotation").checked;
  instance.update();
  addEventLog("切换旋转控制", { enabled: instance.showRotation });
}

// 样式更新
function updateStyle() {
  instance.strokeStyle = document.getElementById("strokeStyle").value;
  instance.fillStyle = document.getElementById("fillStyle").value + "40"; // 添加透明度
  instance.lineWidth = parseInt(document.getElementById("lineWidth").value);
  instance.ctrlRadius = parseInt(document.getElementById("ctrlRadius").value);

  document.getElementById("lineWidthValue").textContent = instance.lineWidth;
  document.getElementById("ctrlRadiusValue").textContent = instance.ctrlRadius;

  instance.update();
  addEventLog("更新样式", {
    strokeStyle: instance.strokeStyle,
    lineWidth: instance.lineWidth
  });
}

function updateBrushStyle() {
  instance.brushStokeStyle = document.getElementById("brushColor").value;
  instance.brushSize = parseInt(document.getElementById("brushSize").value);

  document.getElementById("brushSizeValue").textContent = instance.brushSize;

  addEventLog("更新画笔样式", {
    color: instance.brushStokeStyle,
    size: instance.brushSize
  });
}

function updateEraserStyle() {
  instance.eraserSize = parseInt(document.getElementById("eraserSize").value);
  document.getElementById("eraserSizeValue").textContent = instance.eraserSize;

  addEventLog("更新橡皮擦大小", { size: instance.eraserSize });
}

function updateLabelStyle() {
  instance.labelFont = document.getElementById("labelFont").value;
  instance.labelFillStyle = document.getElementById("labelFillStyle").value;
  instance.textFillStyle = document.getElementById("textFillStyle").value;
  instance.hideLabel = document.getElementById("hideLabel").checked;
  instance.labelUp = document.getElementById("labelUp").checked;

  instance.update();
  addEventLog("更新标签样式", {
    font: instance.labelFont,
    hideLabel: instance.hideLabel
  });
}

// 数据操作
function loadSampleData() {
  const sampleData = [
    {
      label: "示例矩形",
      coor: [
        [100, 100],
        [200, 150]
      ],
      type: 1,
      strokeStyle: "#ff0000",
      fillStyle: "rgba(255, 0, 0, 0.2)"
    },
    {
      label: "示例多边形",
      coor: [
        [250, 120],
        [280, 100],
        [320, 130],
        [300, 170],
        [260, 160]
      ],
      type: 2,
      strokeStyle: "#00ff00",
      fillStyle: "rgba(0, 255, 0, 0.2)"
    },
    {
      label: "示例点",
      coor: [350, 200],
      type: 3,
      strokeStyle: "#0000ff"
    },
    {
      label: "示例折线",
      coor: [
        [400, 100],
        [450, 120],
        [480, 90],
        [520, 110]
      ],
      type: 4,
      strokeStyle: "#ff00ff"
    },
    {
      label: "示例圆形",
      coor: [150, 250],
      radius: 40,
      type: 5,
      strokeStyle: "#ffff00",
      fillStyle: "rgba(255, 255, 0, 0.2)"
    },
    {
      label: "示例网格",
      coor: [
        [300, 250],
        [400, 320]
      ],
      type: 6,
      row: 3,
      col: 2,
      selected: [1, 3],
      strokeStyle: "#00ffff"
    }
  ];

  instance.setData(sampleData);
  addEventLog("加载示例数据", { count: sampleData.length });
  showToast("示例数据加载完成！", "success");
}

function clearAllData() {
  if (confirm("确定要清空所有标注数据吗？")) {
    instance.setData([]);
    addEventLog("清空所有数据", {});
    showToast("所有数据已清空！", "success");
  }
}

function exportData() {
  const data = JSON.stringify(instance.dataset, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `canvas-select-data-${new Date().getTime()}.json`;
  a.click();
  URL.revokeObjectURL(url);

  addEventLog("导出数据", { count: instance.dataset.length });
  showToast("数据导出完成！", "success");
}

function importData() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".json";
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          instance.setData(data);
          addEventLog("导入数据", { count: data.length });
          showToast("数据导入完成！", "success");
        } catch (error) {
          showToast("数据格式错误！", "error");
        }
      };
      reader.readAsText(file);
    }
  };
  input.click();
}

function deleteSelected() {
  const activeShape = instance.activeShape;
  if (activeShape && activeShape.index !== undefined) {
    instance.deleteByIndex(activeShape.index);
    showToast("已删除选中标注！", "success");
  } else {
    showToast("请先选中要删除的标注！", "warning");
  }
}

function clearBrush() {
  instance.clearBrush();
  addEventLog("清除画笔数据", {});
  showToast("画笔数据已清除！", "success");
}

// 图片操作
function changeImage() {
  const url = document.getElementById("imageUrl").value;
  if (url) {
    instance.setImage(url);
    addEventLog("更换图片", { url });
  } else {
    showToast("请输入图片URL！", "warning");
  }
}

function loadLocalImage() {
  document.getElementById("fileInput").click();
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        instance.setImage(img);
        addEventLog("加载本地图片", { name: file.name });
        showToast("本地图片加载完成！", "success");
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  } else {
    showToast("请选择有效的图片文件！", "error");
  }
}

// UI更新函数
function updateUI() {
  updateScaleInfo();
  updateShapeCount(instance.dataset.length);

  // 更新创建类型按钮状态
  setCreateType(instance.createType);

  // 更新复选框状态
  document.getElementById("showCross").checked = instance.showCross;
  document.getElementById("scrollZoom").checked = instance.scrollZoom;
  document.getElementById("readonly").checked = instance.readonly;
  document.getElementById("lock").checked = instance.lock;
  document.getElementById("showRotation").checked = instance.showRotation;
  document.getElementById("hideLabel").checked = instance.hideLabel;
  document.getElementById("labelUp").checked = instance.labelUp;
}

function updateScaleInfo() {
  const scale = Math.round(instance.scale * 100);
  document.getElementById("scaleInfo").textContent = `${scale}%`;
}

function updateShapeCount(count) {
  document.getElementById("shapeCount").textContent = count;
}

function updateDataOutput(data) {
  const output = document.getElementById("dataOutput");
  if (data && data.length > 0) {
    output.textContent = JSON.stringify(data, null, 2);
  } else {
    output.textContent = "暂无标注数据";
  }
}

// 事件日志
function addEventLog(event, data) {
  const timestamp = new Date().toLocaleTimeString();
  eventLog.unshift({ timestamp, event, data });

  if (eventLog.length > maxLogItems) {
    eventLog = eventLog.slice(0, maxLogItems);
  }

  updateEventLogDisplay();
}

function updateEventLogDisplay() {
  const logContainer = document.getElementById("eventLog");
  logContainer.innerHTML = eventLog
    .map(
      (log) =>
        `<div class="event-item">
          <strong>${log.timestamp}</strong> - ${log.event}
          ${
            Object.keys(log.data).length > 0
              ? `<br><small>${JSON.stringify(log.data)}</small>`
              : ""
          }
        </div>`
    )
    .join("");
}

// 工具函数
function getShapeTypeName(type) {
  const typeNames = {
    1: "矩形",
    2: "多边形",
    3: "点",
    4: "折线",
    5: "圆形",
    6: "网格",
    7: "画笔",
    8: "橡皮擦"
  };
  return typeNames[type] || "未知";
}

function showToast(message, type = "success") {
  console.info("::canvas-select事件", message);
}

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", init);

// 窗口大小改变时重新调整
window.addEventListener("resize", () => {
  if (instance) {
    instance.resize();
  }
});
