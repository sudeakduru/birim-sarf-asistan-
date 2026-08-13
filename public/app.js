// Global State
let modeller = [];
let costChartInstance = null;
let recognition = null;
let isListening = false;
let stagedFile = null;
let currentMeasurementKeys = [];
let measurementKeyLabels = {};

// AI Training Tracking Variables
let lastParsedData = null;
let lastParsedFileName = null;


// API Endpoints Base
const API_BASE = "";

// Dynamic Size Groups Definition
const SIZE_GROUPS = {
    adult: ["XS", "S", "M", "L", "XL", "XXL"],
    child1: ["5y-6y", "6y-7y", "7y-8y", "8y-9y", "9y-10y", "10y-11y", "11y-12y", "12y-13y", "13y-14y"],
    child2: ["9-12m", "1-2y", "2-3y", "3-4y", "4-5y", "5-6y", "6-7y", "7-8y"],
    custom: []
};

const KEY_TRANSLATIONS = {
    bel: "Bel Genişliği",
    basen: "Basen Genişliği",
    yan_boy: "Yan Boy",
    on_ag: "Ön Ağ",
    paca_eni: "Paça Eni",
    gogus: "Göğüs Genişliği",
    boy: "Omuzdan Boy (HPS)",
    kol_boyu: "Kol Boyu",
    etek_eni: "Etek Genişliği",
    ic_ag: "İç Ağ / İç Boy",
    ust_bel_yeri_omuz_basindan_on: "Üst Bel Yeri - Ön (Omuz Başından)",
    ust_bel_yeri_omuz_basindan_arka: "Üst Bel Yeri - Arka (Omuz Başından)",
    omuzdan_omuza: "Omuzdan Omuza",
    on_genislik_yeri_omuz_basindan: "Ön Genişlik Yeri (Omuz Başından)",
    on_genislik: "Ön Genişlik",
    arka_genislik_yeri_omuz_basindan: "Arka Genişlik Yeri (Omuz Başından)",
    arka_genislik: "Arka Genişlik",
    kolevi_duz_kolsuz: "Kolevi (Düz / Kolsuz)",
    yaka_acikligi_icten_ice: "Yaka Açıklığı (İçten İçe)",
    yaka_dusuklugu_on_omuz_basindan: "Yaka Düşüklüğü - Ön (Omuz Başından)",
    yaka_dusuklugu_arka_omuz_basindan: "Yaka Düşüklüğü - Arka (Omuz Başından)",
    aski_eni: "Askı Eni",
    pat_genisligi: "Pat Genişliği",
    dugme_citcit_sayisi: "Düğme / Çıtçıt Sayısı",
    son_dugme_yeri_etek_ucundan: "Son Düğme Yeri (Etek Ucundan)",
    firfir_volan_eni_en_genis_nokta: "Fırfır/Volan Eni (En Geniş Nokta)",
    biye_eni_kolevi: "Biye Eni (Kolevi)",
    donus_mesafesi_one_omuz_basindan: "Dönüş Mesafesi - Öne (Omuz Başından)",
    yaka_ucu_yuksekligi: "Yaka Ucu Yüksekliği",
    yaka_yuksekligi: "Yaka Yüksekliği",
    biye_eni: "Biye Eni",
    yirtmac_acikligi: "Yırtmaç Açıklığı",
    iki_yaka_ucu_mesafe_ilikliyken: "İki Yaka Ucu Mesafe (İlikliyken)",
    dantel_yuksekligi: "Dantel Yüksekliği",
    w14: "Bel Kavisli Genişliği (Üstten)",
    w13: "Bel Genişliği (Kavisli Alttan)",
    b04: "Kemer Yüksekliği",
    w17: "Basen Düşüklüğü",
    w59: "Basen Genişliği",
    w20: "Baldır Genişliği",
    l19: "Ön Ağ Uzunluğu",
    l21: "Arka Ağ Uzunluğu",
    w178: "Paça Genişliği",
    l103: "İç Boy",
    n23: "Köprü Eni",
    n22: "Köprü Boyu",
    n32: "Patlet Eni",
    n31: "Patlet Boyu",
    a14: "Fermuar Boyu",
    p292: "Yan Cep Açıklığı",
    bel_kavisli_genisligi_ustten: "Bel Kavisli Genişliği (Üstten)",
    bel_genisligi_kavisli_alttan: "Bel Genişliği (Kavisli Alttan)",
    basen_genisligi: "Basen Genişliği",
    basen_dusuklugu_kemer_dahil_yan: "Basen Düşüklüğü (Kemer Dahil-Yan)",
    on_ag_uzunlugu_kemer_dahil: "Ön Ağ Uzunluğu (Kemer Dahil)",
    arka_ag_uzunlugu_kemer_dahil: "Arka Ağ Uzunluğu (Kemer Dahil)",
    paca_genisligi_ic_boy_16_40_cm_arasi: "Paça Genişliği (İç Boy 16-40 cm)",
    ic_boy_40_cm_alti: "İç Boy (40 cm altı)",
    kopru_eni: "Köprü Eni",
    kopru_boyu: "Köprü Boyu",
    patlet_eni: "Patlet Eni",
    patlet_boyu: "Patlet Boyu",
    fermuar_boyu: "Fermuar Boyu",
    yan_cep_acikligi_5_cep: "Yan Cep Açıklığı (5 Cep)",
    arka_ag: "Arka Ağ",
    baldir_genisligi: "Baldır Genişliği",
    kemer_yuksekligi: "Kemer Yüksekliği",
    yaka_acikligi: "Yaka Açıklığı",
    cep_boyu: "Cep Boyu",
    firfir_eni: "Fırfır Eni"
};

// DOM Elements
const kumasEnInput = document.getElementById("kumasEn");
const modelSelect = document.getElementById("modelSelect");
const cekmeEnInput = document.getElementById("cekmeEn");
const cekmeBoyInput = document.getElementById("cekmeBoy");

const sizeGroupSelect = document.getElementById("sizeGroupSelect");
const verimlilikInput = document.getElementById("verimlilikInput");
const sizeChipsContainer = document.getElementById("sizeChipsContainer");
const asortiContainer = document.getElementById("asortiContainer");
const addCustomSizeBtn = document.getElementById("addCustomSizeBtn");
let customSizes = [];

const calculateBtn = document.getElementById("calculateBtn");
const clearFormBtn = document.getElementById("clearFormBtn");

const metricBirimTuketim = document.getElementById("metricBirimTuketim");
const metricPastalBoyu = document.getElementById("metricPastalBoyu");
const valNetMetraj = document.getElementById("valNetMetraj");
const valCekmeFaktoru = document.getElementById("valCekmeFaktoru");
const valToplamAsorti = document.getElementById("valToplamAsorti");
const valVerimlilik = document.getElementById("valVerimlilik");

// Astar (Lining) DOM Elements
const astarHesapla = document.getElementById("astarHesapla");
const astarInputsContainer = document.getElementById("astarInputsContainer");
const astarEnInput = document.getElementById("astarEn");
const astarCekmeEnInput = document.getElementById("astarCekmeEn");
const astarCekmeBoyInput = document.getElementById("astarCekmeBoy");
const valAstarBirimCard = document.getElementById("valAstarBirimCard");
const valAstarPastalCard = document.getElementById("valAstarPastalCard");
const valAstarBirim = document.getElementById("valAstarBirim");
const valAstarPastal = document.getElementById("valAstarPastal");

// Tül (Tulle) DOM Elements
const tulHesapla = document.getElementById("tulHesapla");
const tulInputsContainer = document.getElementById("tulInputsContainer");
const tulEnInput = document.getElementById("tulEn");
const tulCekmeEnInput = document.getElementById("tulCekmeEn");
const tulCekmeBoyInput = document.getElementById("tulCekmeBoy");
const valTulBirimCard = document.getElementById("valTulBirimCard");
const valTulPastalCard = document.getElementById("valTulPastalCard");
const valTulBirim = document.getElementById("valTulBirim");
const valTulPastal = document.getElementById("valTulPastal");

// Cep (Pocket) DOM Elements
const cepKumastan = document.getElementById("cepKumastan");
const valCepBirimCard = document.getElementById("valCepBirimCard");
const valCepPastalCard = document.getElementById("valCepPastalCard");
const valCepBirim = document.getElementById("valCepBirim");
const valCepPastal = document.getElementById("valCepPastal");

// Feedback Panel Elements
const feedbackPanel = document.getElementById("feedbackPanel");
const feedbackCalismaId = document.getElementById("feedbackCalismaId");
const feedbackTuketim = document.getElementById("feedbackTuketim");
const feedbackAstarTuketim = document.getElementById("feedbackAstarTuketim");
const feedbackTulTuketim = document.getElementById("feedbackTulTuketim");
const feedbackKumasEni = document.getElementById("feedbackKumasEni");
const feedbackCekmeEn = document.getElementById("feedbackCekmeEn");
const feedbackCekmeBoy = document.getElementById("feedbackCekmeBoy");
const saveFeedbackBtn = document.getElementById("saveFeedbackBtn");
const clearFeedbackBtn = document.getElementById("clearFeedbackBtn");

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const fileBtn = document.getElementById("fileBtn");
const fileInput = document.getElementById("fileInput");

const historyToggle = document.getElementById("historyToggle");
const historyHeader = document.getElementById("historyHeader");
const historyContent = document.getElementById("historyContent");
const historyCount = document.getElementById("historyCount");
const historyTableBody = document.getElementById("historyTableBody");

const modelModal = document.getElementById("modelModal");
const modelModalClose = document.getElementById("modelModalClose");
const addModelBtn = document.getElementById("addModelBtn");
const deleteModelBtn = document.getElementById("deleteModelBtn");
const modelCancelBtn = document.getElementById("modelCancelBtn");
const modelForm = document.getElementById("modelForm");

// Initialization
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("initialTime").innerText = getCurrentTime();
    
    loadModeller();
    loadHistory();
    setupSpeechRecognition();
    initChart([], []);
    
    // Populate Initial Size Inputs
    renderAsortiInputs("adult");
    
    // Event Listeners
    calculateBtn.addEventListener("click", handleCalculate);
    clearFormBtn.addEventListener("click", clearForm);
    sendBtn.addEventListener("click", handleSendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSendMessage();
    });
    
    sizeGroupSelect.addEventListener("change", (e) => {
        renderAsortiInputs(e.target.value);
    });
    
    astarHesapla.addEventListener("change", () => {
        astarInputsContainer.style.display = astarHesapla.checked ? "block" : "none";
    });
    
    tulHesapla.addEventListener("change", () => {
        tulInputsContainer.style.display = tulHesapla.checked ? "block" : "none";
    });
    
    modelSelect.addEventListener("change", () => {
        const modelId = modelSelect.value;
        const model = modeller.find(m => m.Model_ID == modelId);
        if (model) {
            resetMeasurementKeysForGroup(model.Urun_Grubu);
        }
        renderMeasurementsTable();
    });
    
    addCustomSizeBtn.addEventListener("click", () => {
        const sizeName = prompt("Eklemek istediğiniz beden adını yazın (Örn: 3XL, 18-24m, 4y-5y):");
        if (sizeName) {
            const cleanName = sizeName.trim();
            if (cleanName) {
                if (!customSizes.includes(cleanName)) {
                    customSizes.push(cleanName);
                }
                const currentVals = getActiveAsortiValues();
                currentVals[cleanName] = 0;
                renderAsortiInputs("custom", currentVals);
                
                setTimeout(() => {
                    const inp = asortiContainer.querySelector(`input[data-size="${cleanName}"]`);
                    if (inp) inp.focus();
                }, 50);
            }
        }
    });
    
    fileBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileUpload);
    saveFeedbackBtn.addEventListener("click", handleSaveFeedback);
    clearFeedbackBtn.addEventListener("click", handleClearFeedback);
    
    historyHeader.addEventListener("click", () => {
        historyContent.classList.toggle("collapsed");
        historyToggle.classList.toggle("collapsed");
        historyToggle.innerText = historyToggle.innerText === "▲" ? "▼" : "▲";
    });
    
    addModelBtn.addEventListener("click", () => modelModal.style.display = "flex");
    deleteModelBtn.addEventListener("click", handleDeleteModel);
    modelModalClose.addEventListener("click", () => modelModal.style.display = "none");
    modelCancelBtn.addEventListener("click", () => modelModal.style.display = "none");
    modelForm.addEventListener("submit", handleAddModel);

    // Tab Navigation Logic
    const tabWorkspace = document.getElementById("tabWorkspace");
    const tabAiTraining = document.getElementById("tabAiTraining");
    const viewWorkspace = document.getElementById("viewWorkspace");
    const viewAiTraining = document.getElementById("viewAiTraining");

    if (tabWorkspace && tabAiTraining) {
        tabWorkspace.addEventListener("click", () => {
            viewWorkspace.style.display = "block";
            viewAiTraining.style.display = "none";
            tabWorkspace.className = "btn btn-primary";
            tabWorkspace.style.border = "none";
            tabWorkspace.style.background = "";
            
            tabAiTraining.className = "btn btn-secondary";
            tabAiTraining.style.border = "1px solid var(--border-glass)";
            tabAiTraining.style.background = "rgba(255, 255, 255, 0.04)";
        });

        tabAiTraining.addEventListener("click", () => {
            viewWorkspace.style.display = "none";
            viewAiTraining.style.display = "block";
            tabAiTraining.className = "btn btn-primary";
            tabAiTraining.style.border = "none";
            tabAiTraining.style.background = "";
            
            tabWorkspace.className = "btn btn-secondary";
            tabWorkspace.style.border = "1px solid var(--border-glass)";
            tabWorkspace.style.background = "rgba(255, 255, 255, 0.04)";
            
            loadAiTrainingHistory();
        });
    }

    // Manual Rule Save
    const saveManualRuleBtn = document.getElementById("saveManualRuleBtn");
    const manualRuleText = document.getElementById("manualRuleText");
    if (saveManualRuleBtn && manualRuleText) {
        saveManualRuleBtn.addEventListener("click", async () => {
            const ruleText = manualRuleText.value.trim();
            if (!ruleText) {
                alert("Lütfen bir kural açıklaması yazın.");
                return;
            }
            try {
                const reqBody = {
                    tip: "analiz_kurali",
                    hatalar: "Manuel Kural",
                    dogrular: ruleText
                };
                const response = await fetch(`${API_BASE}/api/ogrenme`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(reqBody)
                });
                
                if (response.ok) {
                    manualRuleText.value = "";
                    loadAiTrainingHistory();
                } else {
                    alert("Kural kaydedilirken bir hata oluştu.");
                }
            } catch (err) {
                console.error("Manual rule save error:", err);
                alert("Sunucuya bağlanırken hata oluştu.");
            }
        });
    }
});

function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');
}

// -------------------------------------------------------------------------
// DYNAMIC SIZE RENDERERS & MEASUREMENTS TABLE
// -------------------------------------------------------------------------

function renderAsortiInputs(groupName, values = {}) {
    sizeChipsContainer.innerHTML = "";
    asortiContainer.innerHTML = "";
    
    addCustomSizeBtn.style.display = (groupName === "custom") ? "block" : "none";
    
    const standardSizes = SIZE_GROUPS[groupName] || [];
    const valueKeys = Object.keys(values);
    const hasValues = valueKeys.length > 0;
    
    if (groupName === "custom") {
        valueKeys.forEach(k => {
            if (!customSizes.includes(k)) {
                customSizes.push(k);
            }
        });
    }
    
    const sizesToShow = groupName === "custom" ? customSizes : standardSizes;
    
    if (sizesToShow.length === 0 && groupName === "custom") {
        asortiContainer.innerHTML = `
            <p style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; width: 100%; text-align: center; padding: 10px 0;">
                Beden eklemek için "+ Özel Ekle" butonuna basın veya chat üzerinden dosya yükleyin.
            </p>
        `;
        return;
    }
    
    sizesToShow.forEach(size => {
        const val = values[size] !== undefined ? values[size] : 0;
        let isActive = hasValues ? (values[size] !== undefined) : true;
        
        const chip = document.createElement("div");
        chip.className = `size-chip${isActive ? " active" : ""}`;
        chip.setAttribute("data-size", size);
        chip.innerHTML = `<span>${size}</span>`;
        
        if (groupName === "custom") {
            const removeSpan = document.createElement("span");
            removeSpan.className = "chip-remove";
            removeSpan.innerHTML = "×";
            removeSpan.addEventListener("click", (e) => {
                e.stopPropagation();
                customSizes = customSizes.filter(s => s !== size);
                const currentVals = getActiveAsortiValues();
                delete currentVals[size];
                renderAsortiInputs("custom", currentVals);
            });
            chip.appendChild(removeSpan);
        }
        
        chip.addEventListener("click", () => {
            chip.classList.toggle("active");
            updateAsortiInputsFromChips(groupName);
        });
        
        sizeChipsContainer.appendChild(chip);
        
        if (isActive) {
            createSizeInputField(size, val);
        }
    });
    
    renderMeasurementsTable();
}

function updateAsortiInputsFromChips(groupName) {
    const currentValues = getActiveAsortiValues();
    asortiContainer.innerHTML = "";
    
    const activeChips = sizeChipsContainer.querySelectorAll(".size-chip.active");
    if (activeChips.length === 0) {
        asortiContainer.innerHTML = `
            <p style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; width: 100%; text-align: center; padding: 10px 0;">
                Miktar girmek için yukarıdan en az bir beden aktif edin.
            </p>
        `;
        renderMeasurementsTable();
        return;
    }
    
    activeChips.forEach(chip => {
        const size = chip.getAttribute("data-size");
        const val = currentValues[size] !== undefined ? currentValues[size] : 0;
        createSizeInputField(size, val);
    });
    
    renderMeasurementsTable();
}

function getActiveAsortiValues() {
    const values = {};
    const inputs = asortiContainer.querySelectorAll(".asorti-val-input");
    inputs.forEach(inp => {
        const size = inp.getAttribute("data-size");
        const val = parseInt(inp.value) || 0;
        values[size] = val;
    });
    return values;
}

function createSizeInputField(sizeName, value = 0) {
    const div = document.createElement("div");
    div.className = "form-group asorti-input";
    div.style.width = "75px";
    div.style.alignItems = "center";
    div.style.gap = "4px";
    
    div.innerHTML = `
        <label style="font-size: 0.8rem; font-weight: 700; color: var(--text-main);">${sizeName}</label>
        <input type="number" class="asorti-val-input" data-size="${sizeName}" min="0" value="${value}" style="width: 100%; text-align: center; padding: 8px;">
    `;
    asortiContainer.appendChild(div);
}

function resetMeasurementKeysForGroup(urunGrubu) {
    const ug = urunGrubu.toLowerCase().replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ç/g, 'c');
    let defaultKeys = [];
    let defaultLabels = {};
    
    if (ug.includes("alt")) {
        defaultKeys = ["bel", "basen", "yan_boy", "on_ag", "paca_eni"];
    } else if (ug.includes("ust") || ug.includes("orme")) {
        defaultKeys = ["gogus", "boy", "kol_boyu"];
    } else if (ug.includes("elbise")) {
        defaultKeys = ["gogus", "basen", "boy", "kol_boyu", "etek_eni"];
    } else if (ug.includes("tulum")) {
        defaultKeys = ["gogus", "basen", "boy", "ic_ag", "kol_boyu", "paca_eni"];
    } else {
        defaultKeys = ["bel", "basen", "yan_boy"];
    }
    
    defaultKeys.forEach(k => {
        defaultLabels[k] = KEY_TRANSLATIONS[k] || k.charAt(0).toUpperCase() + k.slice(1).replace(/_/g, " ");
    });
    
    currentMeasurementKeys = [...defaultKeys];
    measurementKeyLabels = { ...defaultLabels };
}

function normalizeOlculer(olculerData) {
    if (!olculerData || typeof olculerData !== "object") return {};
    
    const normalized = {};
    const ALIAS_MAP = {
        "bel_kavisli_genisligi_ustten": "bel",
        "bel_genisligi_kavisli_alttan": "bel",
        "bel_genisligi": "bel",
        "w14": "bel", "w13": "bel", "w222": "bel", "waist": "bel",
        "basen_genisligi": "basen", "w59": "basen", "hip": "basen", "hips": "basen",
        "on_ag_uzunlugu_kemer_dahil": "on_ag", "on_ag_uzunlugu": "on_ag", "l19": "on_ag", "front_rise": "on_ag",
        "arka_ag_uzunlugu_kemer_dahil": "arka_ag", "arka_ag_uzunlugu": "arka_ag", "l21": "arka_ag", "back_rise": "arka_ag",
        "ic_boy_40_cm_alti": "ic_ag", "ic_boy_40cm_alti": "ic_ag", "ic_boy": "ic_ag", "l103": "ic_ag", "l259": "ic_ag", "inseam": "ic_ag",
        "paca_genisligi_ic_boy_16_40_cm_arasi": "paca_eni", "paca_genisligi": "paca_eni", "w178": "paca_eni", "w252": "paca_eni", "hem_width": "paca_eni",
        "kemer_yuksekligi": "kemer_yuksekligi", "b04": "kemer_yuksekligi",
        "basen_dusuklugu_kemer_dahil_yan": "basen_dusuklugu", "basen_dusuklugu_kemer_dahil": "basen_dusuklugu", "w17": "basen_dusuklugu", "basen_drop": "basen_dusuklugu",
        "baldir_genisligi": "baldir_genisligi", "w20": "baldir_genisligi",
        "gogus_genisligi": "gogus", "gogus_eni": "gogus", "w221": "gogus", "chest": "gogus",
        "omuzdan_boy_hps": "boy", "omuzdan_boy": "boy", "l04": "boy",
        "kol_boyu_uzun_arka_ortadan": "kol_boyu", "s53": "kol_boyu", "sleeve_length": "kol_boyu",
        "etek_ucu_genisligi": "etek_eni", "w105": "etek_eni"
    };

    Object.entries(olculerData).forEach(([size, params]) => {
        if (!params || typeof params !== "object") return;
        normalized[size] = {};
        
        Object.entries(params).forEach(([rawKey, val]) => {
            const numVal = parseFloat(val) || 0;
            const lowerKey = rawKey.toLowerCase();
            const standardKey = ALIAS_MAP[lowerKey];
            
            if (standardKey) {
                if (normalized[size][standardKey] === undefined || numVal > normalized[size][standardKey]) {
                    normalized[size][standardKey] = numVal;
                }
            } else {
                normalized[size][rawKey] = numVal;
            }
        });
        
        if (!normalized[size]["yan_boy"] && normalized[size]["on_ag"] && normalized[size]["ic_ag"]) {
            normalized[size]["yan_boy"] = parseFloat((normalized[size]["on_ag"] + normalized[size]["ic_ag"]).toFixed(1));
        }
    });

    return normalized;
}

function mergeMeasurementKeys(olculerData) {
    if (!olculerData) return;
    
    const allKeys = new Set(currentMeasurementKeys);
    
    Object.values(olculerData).forEach(sizeObj => {
        if (sizeObj && typeof sizeObj === "object") {
            Object.keys(sizeObj).forEach(k => {
                allKeys.add(k);
                if (!measurementKeyLabels[k]) {
                    if (KEY_TRANSLATIONS[k]) {
                        measurementKeyLabels[k] = KEY_TRANSLATIONS[k];
                    } else {
                        let cleanLabel = k.replace(/_/g, " ");
                        cleanLabel = cleanLabel.charAt(0).toUpperCase() + cleanLabel.slice(1);
                        measurementKeyLabels[k] = cleanLabel;
                    }
                }
            });
        }
    });
    
    currentMeasurementKeys = Array.from(allKeys);
}

function renderFeedbackAsortiGrid(study) {
    const feedbackAsortiGrid = document.getElementById("feedbackAsortiGrid");
    if (!feedbackAsortiGrid) return;
    feedbackAsortiGrid.innerHTML = "";
    
    let plannedAsorti = {};
    try {
        plannedAsorti = JSON.parse(study.Asorti_JSON || "{}");
    } catch(e) {
        console.error("Error parsing planned asorti:", e);
    }
    
    let realizedAsorti = {};
    try {
        realizedAsorti = JSON.parse(study.Gerceklesen_Asorti_JSON || "{}");
    } catch(e) {
        console.error("Error parsing realized asorti:", e);
    }
    
    const sizes = Object.keys(plannedAsorti);
    if (sizes.length === 0) {
        document.getElementById("feedbackAsortiContainer").style.display = "none";
        return;
    }
    
    document.getElementById("feedbackAsortiContainer").style.display = "block";
    
    sizes.forEach(size => {
        const plannedQty = plannedAsorti[size];
        const currentVal = realizedAsorti[size] !== undefined ? realizedAsorti[size] : plannedQty;
        
        const sizeCol = document.createElement("div");
        sizeCol.style.display = "flex";
        sizeCol.style.flexDirection = "column";
        sizeCol.style.gap = "4px";
        
        sizeCol.innerHTML = `
            <span style="font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-align: center;">${size}</span>
            <input type="number" class="feedback-asorti-input" data-size="${size}" value="${currentVal}" min="0" step="1" 
                   style="padding: 6px; text-align: center; font-size: 0.8rem; border-radius: 4px; border: 1px solid var(--border-glass); background: rgba(255,255,255,0.05); color: #fff; width: 100%;">
        `;
        feedbackAsortiGrid.appendChild(sizeCol);
    });
}

function renderMeasurementsTable(overrideValues = null) {
    const container = document.getElementById("measurementsTableContainer");
    if (!container) return;
    
    const modelId = modelSelect.value;
    if (!modelId) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; text-align: center; padding: 10px 0;">Lütfen önce bir model seçin.</p>`;
        return;
    }
    
    const model = modeller.find(m => m.Model_ID == modelId);
    if (!model) return;
    
    if (currentMeasurementKeys.length === 0) {
        resetMeasurementKeysForGroup(model.Urun_Grubu);
    }
    
    const activeChips = sizeChipsContainer.querySelectorAll(".size-chip.active");
    const activeSizes = Array.from(activeChips).map(chip => chip.getAttribute("data-size"));
    
    if (activeSizes.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; text-align: center; padding: 10px 0;">Lütfen yukarıdan en az bir beden seçin.</p>`;
        return;
    }
    
    const oldValues = {};
    const inputs = container.querySelectorAll(".measurement-input");
    inputs.forEach(inp => {
        const size = inp.getAttribute("data-size");
        const param = inp.getAttribute("data-param");
        if (!oldValues[size]) oldValues[size] = {};
        oldValues[size][param] = inp.value;
    });

    if (overrideValues && typeof overrideValues === "object") {
        Object.entries(overrideValues).forEach(([sz, params]) => {
            if (params && typeof params === "object") {
                if (!oldValues[sz]) oldValues[sz] = {};
                Object.entries(params).forEach(([p, val]) => {
                    oldValues[sz][p] = val;
                });
            }
        });
    }
    
    let html = `<table class="measurements-grid-table" style="width: 100%; border-collapse: collapse; margin-top: 10px;">`;
    html += `<thead><tr><th style="text-align: left; padding: 8px; border-bottom: 2px solid var(--border-glass);">Ölçüm Alanı</th>`;
    activeSizes.forEach(size => {
        html += `<th style="text-align: center; padding: 8px; border-bottom: 2px solid var(--border-glass);">${size}</th>`;
    });
    html += `</tr></thead><tbody>`;
    
    const urunGrubu = model.Urun_Grubu ? model.Urun_Grubu.toLowerCase().replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ç/g, 'c') : "";
    const defaultVals = {
        bel: 60, basen: 80, yan_boy: 30, on_ag: 20, paca_eni: 25,
        gogus: 50, boy: 65,
        kol_boyu: (urunGrubu.includes("ust") || urunGrubu.includes("orme")) ? 20 : 0,
        etek_eni: urunGrubu.includes("elbise") ? 60 : 0,
        ic_ag: 65
    };
    
    currentMeasurementKeys.forEach(p => {
        const label = measurementKeyLabels[p] || p;
        html += `<tr><td style="padding: 8px; border-bottom: 1px solid var(--border-glass); font-weight: bold; text-align: left;">${label}</td>`;
        activeSizes.forEach(size => {
            let val = defaultVals[p] || 0;
            if (oldValues[size] && oldValues[size][p] !== undefined) {
                val = oldValues[size][p];
            }
            html += `<td style="padding: 8px; border-bottom: 1px solid var(--border-glass); text-align: center;">
                <input type="number" step="0.1" min="0" class="measurement-input" data-size="${size}" data-param="${p}" value="${val}" style="width: 80px; text-align: center; padding: 6px; border-radius: 4px; border: 1px solid var(--border-glass); background: rgba(255,255,255,0.05); color: var(--text-main);">
            </td>`;
        });
        html += `</tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function getMeasurementsValues() {
    const values = {};
    const inputs = document.querySelectorAll(".measurement-input");
    inputs.forEach(inp => {
        const size = inp.getAttribute("data-size");
        const param = inp.getAttribute("data-param");
        const val = parseFloat(inp.value) || 0.0;
        if (!values[size]) values[size] = {};
        values[size][param] = val;
    });
    return values;
}

// -------------------------------------------------------------------------
// DATABASE LOADERS
// -------------------------------------------------------------------------

async function loadModeller(selectedId = null) {
    try {
        const res = await fetch(`${API_BASE}/api/modeller`);
        modeller = await res.json();
        
        modelSelect.innerHTML = '<option value="" disabled selected>Model seçin...</option>';
        modeller.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.Model_ID;
            opt.innerText = `${m.Model_Adi} (${m.Urun_Grubu})`;
            modelSelect.appendChild(opt);
        });
        
        if (selectedId) {
            modelSelect.value = selectedId;
            const model = modeller.find(m => m.Model_ID == selectedId);
            if (model) {
                resetMeasurementKeysForGroup(model.Urun_Grubu);
            }
            renderMeasurementsTable();
        }
    } catch (e) {
        console.error("Error loading models: ", e);
        showSystemMessage("Hata: Model tanımları yüklenemedi.", "error");
    }
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/calismalar`);
        const calismalar = await res.json();
        
        historyCount.innerText = `${calismalar.length} Kayıt Bulundu`;
        
        if (calismalar.length === 0) {
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="10" class="empty-row-text">Henüz kayıtlı bir çalışma bulunmamaktadır.</td>
                </tr>
            `;
            return;
        }
        
        historyTableBody.innerHTML = "";
        calismalar.forEach(c => {
            const dateStr = new Date(c.Kayit_Tarihi).toLocaleDateString("tr-TR", {
                hour: '2-digit', minute: '2-digit'
            });
            
            const asortiObj = JSON.parse(c.Asorti_JSON || "{}");
            const asortiStr = Object.entries(asortiObj).map(([s, v]) => `${s}:${v}`).join(" | ") || "—";
            
            let kumasStr = `<strong>${c.Kumas_Eni_cm} cm</strong>`;
            if (c.Astar_Eni_cm > 0) {
                kumasStr += `<br><span style="color: var(--color-secondary); font-size: 0.75rem;">Astar: ${c.Astar_Eni_cm} cm</span>`;
            }
            if (c.Tul_Eni_cm > 0) {
                kumasStr += `<br><span style="color: var(--color-accent); font-size: 0.75rem;">Tül: ${c.Tul_Eni_cm} cm</span>`;
            }
            
            let cekmeStr = `En: %${c.Cekme_En_Yuzde.toFixed(1)} / Boy: %${c.Cekme_Boy_Yuzde.toFixed(1)}`;
            if (c.Astar_Eni_cm > 0) {
                cekmeStr += `<br><span style="color: var(--color-secondary); font-size: 0.75rem;">Astar En: %${c.Astar_Cekme_En_Yuzde.toFixed(1)} / Boy: %${c.Astar_Cekme_Boy_Yuzde.toFixed(1)}</span>`;
            }
            if (c.Tul_Eni_cm > 0) {
                cekmeStr += `<br><span style="color: var(--color-accent); font-size: 0.75rem;">Tül En: %${c.Tul_Cekme_En_Yuzde.toFixed(1)} / Boy: %${c.Tul_Cekme_Boy_Yuzde.toFixed(1)}</span>`;
            }
            
            let tuketimCell = `<strong>Plan: ${c.Hesaplanan_Birim_Metraj_M.toFixed(3)} m</strong>`;
            if (c.Astar_Eni_cm > 0) {
                tuketimCell += `<br><span style="color: var(--color-secondary); font-size: 0.75rem;">Astar: ${c.Hesaplanan_Astar_Birim_M.toFixed(3)} m</span>`;
            }
            if (c.Tul_Eni_cm > 0) {
                tuketimCell += `<br><span style="color: var(--color-accent); font-size: 0.75rem;">Tül: ${c.Hesaplanan_Tul_Birim_M.toFixed(3)} m</span>`;
            }
            
            let pastalStr = `${c.Hesaplanan_Pastal_Boyu_M.toFixed(2)} m`;
            if (c.Astar_Eni_cm > 0) {
                pastalStr += `<br><span style="color: var(--color-secondary); font-size: 0.75rem;">Astar: ${c.Hesaplanan_Astar_Pastal_M.toFixed(2)} m</span>`;
            }
            if (c.Tul_Eni_cm > 0) {
                pastalStr += `<br><span style="color: var(--color-accent); font-size: 0.75rem;">Tül: ${c.Hesaplanan_Tul_Pastal_M.toFixed(2)} m</span>`;
            }
            
            let verimlilikVal = c.Verimlilik_Yuzde !== undefined && c.Verimlilik_Yuzde !== null ? c.Verimlilik_Yuzde : 90.0;
            let verimlilikSub = `<br><span style="font-size:0.75rem; color:var(--text-muted);">Verimlilik: %${verimlilikVal.toFixed(1)}</span>`;
            pastalStr += verimlilikSub;

            let gerceklesenCell = "";
            let gercek_kumas = c.Gerceklesen_Birim_Metraj_M !== null && c.Gerceklesen_Birim_Metraj_M !== undefined ? c.Gerceklesen_Birim_Metraj_M.toFixed(3) + ' m' : '—';
            gerceklesenCell += `<strong>Kumaş: ${gercek_kumas}</strong>`;
            if (c.Astar_Eni_cm > 0) {
                let gercek_astar = c.Gerceklesen_Astar_Birim_M !== null && c.Gerceklesen_Astar_Birim_M !== undefined ? c.Gerceklesen_Astar_Birim_M.toFixed(3) + ' m' : '—';
                gerceklesenCell += `<br><span style="color: var(--color-secondary); font-size: 0.75rem;">Astar: ${gercek_astar}</span>`;
            }
            if (c.Tul_Eni_cm > 0) {
                let gercek_tul = c.Gerceklesen_Tul_Birim_M !== null && c.Gerceklesen_Tul_Birim_M !== undefined ? c.Gerceklesen_Tul_Birim_M.toFixed(3) + ' m' : '—';
                gerceklesenCell += `<br><span style="color: var(--color-accent); font-size: 0.75rem;">Tül: ${gercek_tul}</span>`;
            }
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${dateStr}</td>
                <td><strong>${c.Model_Adi}</strong></td>
                <td><strong>${c.Urun_Grubu}</strong></td>
                <td>${kumasStr}</td>
                <td>${cekmeStr}</td>
                <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${asortiStr}"><strong>${asortiStr}</strong></td>
                <td>${tuketimCell}</td>
                <td>${pastalStr}</td>
                <td>${gerceklesenCell}</td>
                <td style="text-align: center;">
                    <button class="btn-row-delete" title="Bu çalışmayı sil" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 1.1rem; padding: 4px; transition: var(--transition-smooth);" onmouseover="this.style.transform='scale(1.2)'; this.style.color='#f87171';" onmouseout="this.style.transform='scale(1)'; this.style.color='#ef4444';">🗑️</button>
                </td>
            `;
            
            tr.style.cursor = "pointer";
            tr.title = "Parametreleri forma geri yüklemek için tıklayın";
            tr.addEventListener("click", () => loadCalismaToForm(c));
            
            const deleteBtn = tr.querySelector(".btn-row-delete");
            deleteBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                handleDeleteCalisma(c.Calisma_ID);
            });
            
            historyTableBody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading history: ", e);
    }
}

async function loadAiTrainingHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/ogrenme`);
        const records = await res.json();
        
        const tbody = document.getElementById("aiTrainingTableBody");
        if (!tbody) return;
        
        if (records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-row-text">Henüz öğrenme kaydı bulunmamaktadır.</td></tr>`;
            return;
        }
        
        tbody.innerHTML = "";
        records.forEach(r => {
            const dateStr = new Date(r.created_at).toLocaleDateString("tr-TR", {
                hour: '2-digit', minute: '2-digit'
            });
            const tr = document.createElement("tr");
            
            if (r.duzeltme_tipi === "analiz_kurali") {
                tr.innerHTML = `
                    <td>${dateStr}</td>
                    <td><strong style="color: #f59e0b;">Manuel Kural</strong></td>
                    <td><div style="font-size: 0.8rem; color: var(--text-muted);">— (Manuel Eklenen Kural) —</div></td>
                    <td><div style="max-height: 100px; overflow-y: auto; font-size: 0.85rem; color: #fcd34d; padding: 4px; border-left: 2px solid #f59e0b;">${r.dogru_veri.replace(/\n/g, '<br>')}</div></td>
                    <td style="text-align: center;">
                        <button class="btn-row-delete-ai" data-id="${r.id}" title="Bu kaydı sil" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 1.1rem; padding: 4px; transition: var(--transition-smooth);" onmouseover="this.style.transform='scale(1.2)'; this.style.color='#f87171';" onmouseout="this.style.transform='scale(1)'; this.style.color='#ef4444';">🗑️</button>
                    </td>
                `;
            } else {
                tr.innerHTML = `
                    <td>${dateStr}</td>
                    <td><strong>${r.duzeltme_tipi === "olcu_duzeltme" ? "Ölçü Düzeltme" : r.duzeltme_tipi}</strong></td>
                    <td><div style="max-height: 100px; overflow-y: auto; font-size: 0.8rem;">${r.hatali_veri.replace(/\n/g, '<br>')}</div></td>
                    <td><div style="max-height: 100px; overflow-y: auto; font-size: 0.8rem; color: var(--color-success);">${r.dogru_veri.replace(/\n/g, '<br>')}</div></td>
                    <td style="text-align: center;">
                        <button class="btn-row-delete-ai" data-id="${r.id}" title="Bu kaydı sil" style="background: transparent; border: none; color: #ef4444; cursor: pointer; font-size: 1.1rem; padding: 4px; transition: var(--transition-smooth);" onmouseover="this.style.transform='scale(1.2)'; this.style.color='#f87171';" onmouseout="this.style.transform='scale(1)'; this.style.color='#ef4444';">🗑️</button>
                    </td>
                `;
            }
            tbody.appendChild(tr);
        });
        
        document.querySelectorAll(".btn-row-delete-ai").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                const id = e.currentTarget.getAttribute("data-id");
                if (confirm("Bu yapay zeka öğrenme kaydını silmek istediğinize emin misiniz?")) {
                    await fetch(`${API_BASE}/api/ogrenme/${id}`, { method: "DELETE" });
                    loadAiTrainingHistory();
                }
            });
        });
    } catch (e) {
        console.error("AI Eğitim verileri yüklenemedi", e);
    }
}

function loadCalismaToForm(study) {
    kumasEnInput.value = study.Kumas_Eni_cm || 175;
    modelSelect.value = study.Model_ID;
    cekmeEnInput.value = study.Cekme_En_Yuzde;
    cekmeBoyInput.value = study.Cekme_Boy_Yuzde;
    
    cepKumastan.checked = study.Cep_Kumastan !== undefined && study.Cep_Kumastan !== null ? !!study.Cep_Kumastan : true;
    
    verimlilikInput.value = study.Verimlilik_Yuzde !== undefined && study.Verimlilik_Yuzde !== null ? study.Verimlilik_Yuzde : 90.0;
    valVerimlilik.innerText = `%${(study.Verimlilik_Yuzde !== undefined && study.Verimlilik_Yuzde !== null ? study.Verimlilik_Yuzde : 90.0).toFixed(1)}`;
    
    if (study.Astar_Eni_cm > 0) {
        astarHesapla.checked = true;
        astarInputsContainer.style.display = "block";
        astarEnInput.value = study.Astar_Eni_cm;
        astarCekmeEnInput.value = study.Astar_Cekme_En_Yuzde;
        astarCekmeBoyInput.value = study.Astar_Cekme_Boy_Yuzde;
        valAstarBirimCard.style.display = "block";
        valAstarPastalCard.style.display = "block";
        valAstarBirim.innerText = `${study.Hesaplanan_Astar_Birim_M.toFixed(3)} m`;
        valAstarPastal.innerText = `${study.Hesaplanan_Astar_Pastal_M.toFixed(2)} m`;
    } else {
        astarHesapla.checked = false;
        astarInputsContainer.style.display = "none";
        valAstarBirimCard.style.display = "none";
        valAstarPastalCard.style.display = "none";
        valAstarBirim.innerText = "0.00 m";
        valAstarPastal.innerText = "0.00 m";
    }
    
    if (study.Tul_Eni_cm > 0) {
        tulHesapla.checked = true;
        tulInputsContainer.style.display = "block";
        tulEnInput.value = study.Tul_Eni_cm;
        tulCekmeEnInput.value = study.Tul_Cekme_En_Yuzde;
        tulCekmeBoyInput.value = study.Tul_Cekme_Boy_Yuzde;
        valTulBirimCard.style.display = "block";
        valTulPastalCard.style.display = "block";
        valTulBirim.innerText = `${study.Hesaplanan_Tul_Birim_M.toFixed(3)} m`;
        valTulPastal.innerText = `${study.Hesaplanan_Tul_Pastal_M.toFixed(2)} m`;
    } else {
        tulHesapla.checked = false;
        tulInputsContainer.style.display = "none";
        valTulBirimCard.style.display = "none";
        valTulPastalCard.style.display = "none";
        valTulBirim.innerText = "0.00 m";
        valTulPastal.innerText = "0.00 m";
    }
    
    feedbackPanel.style.display = "block";
    feedbackCalismaId.value = study.Calisma_ID;
    feedbackTuketim.value = study.Gerceklesen_Birim_Metraj_M !== null && study.Gerceklesen_Birim_Metraj_M !== undefined ? study.Gerceklesen_Birim_Metraj_M : "";
    
    // Astar feedback field display
    if (study.Astar_Eni_cm > 0) {
        document.getElementById("feedbackAstarGroup").style.display = "block";
        feedbackAstarTuketim.value = study.Gerceklesen_Astar_Birim_M !== null && study.Gerceklesen_Astar_Birim_M !== undefined ? study.Gerceklesen_Astar_Birim_M : "";
    } else {
        document.getElementById("feedbackAstarGroup").style.display = "none";
        feedbackAstarTuketim.value = "";
    }
    
    // Tulle feedback field display
    if (study.Tul_Eni_cm > 0) {
        document.getElementById("feedbackTulGroup").style.display = "block";
        feedbackTulTuketim.value = study.Gerceklesen_Tul_Birim_M !== null && study.Gerceklesen_Tul_Birim_M !== undefined ? study.Gerceklesen_Tul_Birim_M : "";
    } else {
        document.getElementById("feedbackTulGroup").style.display = "none";
        feedbackTulTuketim.value = "";
    }
    
    renderFeedbackAsortiGrid(study);
    
    feedbackKumasEni.value = study.Gerceklesen_Kumas_Eni_cm !== null && study.Gerceklesen_Kumas_Eni_cm !== undefined ? study.Gerceklesen_Kumas_Eni_cm : study.Kumas_Eni_cm;
    feedbackCekmeEn.value = study.Gerceklesen_Cekme_En_Yuzde !== null && study.Gerceklesen_Cekme_En_Yuzde !== undefined ? study.Gerceklesen_Cekme_En_Yuzde : study.Cekme_En_Yuzde;
    feedbackCekmeBoy.value = study.Gerceklesen_Cekme_Boy_Yuzde !== null && study.Gerceklesen_Cekme_Boy_Yuzde !== undefined ? study.Gerceklesen_Cekme_Boy_Yuzde : study.Cekme_Boy_Yuzde;
    
    const asortiData = JSON.parse(study.Asorti_JSON || "{}");
    const olculerData = normalizeOlculer(JSON.parse(study.Olculer_JSON || "{}"));
    const keys = Object.keys(asortiData);
    
    // Pocket (Cep) check and display
    const model = modeller.find(m => m.Model_ID == study.Model_ID);
    let hasPockets = false;
    if (model) {
        const urunGrubu = model.Urun_Grubu.toLowerCase().replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ç/g, 'c');
        if (urunGrubu.includes("alt")) {
            let totalCepNetArea = 0.0;
            const activeSizes = Object.keys(asortiData);
            activeSizes.forEach(size => {
                const m = olculerData[size] || {};
                const qty = asortiData[size] || 0;
                const cep_torba_eni = parseFloat(m.on_cep_torba_eni || m.cep_eni || 9.0);
                const cep_torba_boyu = parseFloat(m.on_cep_torba_boyu || m.cep_boyu || 12.0);
                const area_cep = 2.0 * 2.0 * cep_torba_eni * cep_torba_boyu / 10000.0;
                totalCepNetArea += area_cep * qty;
            });
            if (totalCepNetArea > 0) {
                hasPockets = true;
                const totalAsorti = study.Toplam_Asorti_Adet;
                const cep_eni_m = 1.40;
                const cep_verimlilik = Math.max(88.0, study.Verimlilik_Yuzde || 90.0);
                const cep_pastal_boyu = (totalCepNetArea * 1.15) / (cep_eni_m * (cep_verimlilik / 100.0));
                const cep_birim_metraj = cep_pastal_boyu / totalAsorti;
                
                valCepBirimCard.style.display = "block";
                valCepPastalCard.style.display = "block";
                valCepBirim.innerText = `${cep_birim_metraj.toFixed(3)} m`;
                valCepPastal.innerText = `${cep_pastal_boyu.toFixed(2)} m`;
            }
        }
    }
    if (!hasPockets) {
        valCepBirimCard.style.display = "none";
        valCepPastalCard.style.display = "none";
        valCepBirim.innerText = "0.00 m";
        valCepPastal.innerText = "0.00 m";
    }
    let matchedGroup = "custom";
    
    const isAdult = keys.every(k => SIZE_GROUPS.adult.includes(k));
    const isChild1 = keys.every(k => SIZE_GROUPS.child1.includes(k));
    const isChild2 = keys.every(k => SIZE_GROUPS.child2.includes(k));
    
    if (keys.length > 0) {
        if (isAdult) matchedGroup = "adult";
        else if (isChild1) matchedGroup = "child1";
        else if (isChild2) matchedGroup = "child2";
    } else {
        matchedGroup = "adult";
    }
    
    sizeGroupSelect.value = matchedGroup;
    
    if (model) {
        resetMeasurementKeysForGroup(model.Urun_Grubu);
        mergeMeasurementKeys(olculerData);
    }
    
    renderAsortiInputs(matchedGroup, asortiData);
    renderMeasurementsTable(olculerData);
    
    metricBirimTuketim.innerText = `${study.Hesaplanan_Birim_Metraj_M.toFixed(3)} m`;
    metricPastalBoyu.innerText = `${study.Hesaplanan_Pastal_Boyu_M.toFixed(2)} m`;
    valCekmeFaktoru.innerText = `${((1 + study.Cekme_En_Yuzde/100) * (1 + study.Cekme_Boy_Yuzde/100)).toFixed(4)}`;
    valToplamAsorti.innerText = `${study.Toplam_Asorti_Adet} Adet`;
    
    setTimeout(() => {
        const activeChips = sizeChipsContainer.querySelectorAll(".size-chip.active");
        const activeSizes = Array.from(activeChips).map(chip => chip.getAttribute("data-size"));
        const model = modeller.find(m => m.Model_ID == study.Model_ID);
        if (model) {
            const urunGrubu = model.Urun_Grubu.toLowerCase().replace(/ü/g, 'u').replace(/ö/g, 'o').replace(/ı/g, 'i').replace(/ş/g, 's').replace(/ğ/g, 'g').replace(/ç/g, 'c');
            let totalNetArea = 0.0;
            const netAreasList = [];
            const labels = [];
            
            activeSizes.forEach(size => {
                const m = olculerData[size] || {};
                let netArea = 0;
                
                if (urunGrubu.includes("alt")) {
                    const bel = parseFloat(m.bel || 60);
                    const basen = parseFloat(m.basen || 80);
                    const yan_boy = parseFloat(m.yan_boy || 30);
                    const on_ag = parseFloat(m.on_ag || 20);
                    const paca_eni = parseFloat(m.paca_eni || 25);
                    const area_front = 2.0 * ((basen / 4.0 + paca_eni) / 2.0) * (yan_boy - 4.0) * 1.15 / 10000.0;
                    const area_back = 2.0 * ((basen / 4.0 + 4.0 + paca_eni) / 2.0) * (yan_boy - 4.0) * 1.15 / 10000.0;
                    const area_kemer = bel * 8.0 * 1.15 / 10000.0;
                    
                    let area_cep = 0.0;
                    if (cepKumastan.checked) {
                        const cep_torba_eni = parseFloat(m.on_cep_torba_eni || m.cep_eni || 9.0);
                        const cep_torba_boyu = parseFloat(m.on_cep_torba_boyu || m.cep_boyu || 12.0);
                        area_cep = 2.0 * 2.0 * cep_torba_eni * cep_torba_boyu * 1.15 / 10000.0;
                    }
                    
                    netArea = area_front + area_back + area_kemer + area_cep;
                } else if (urunGrubu.includes("ust") || urunGrubu.includes("orme")) {
                    const gogus = parseFloat(m.gogus || 50);
                    const boy = parseFloat(m.boy || 65);
                    const kol_boyu = parseFloat(m.kol_boyu || 20);
                    const area_front = gogus * boy * 1.15 / 10000.0;
                    const area_back = gogus * boy * 1.15 / 10000.0;
                    const area_kol = 2.0 * kol_boyu * (boy / 3.0) * 1.15 / 10000.0;
                    const area_yaka = 0.03;
                    netArea = area_front + area_back + area_kol + area_yaka;
                } else if (urunGrubu.includes("elbise")) {
                    const gogus = parseFloat(m.gogus || 48);
                    const basen = parseFloat(m.basen || 85);
                    const boy = parseFloat(m.boy || 90);
                    const kol_boyu = parseFloat(m.kol_boyu || 0);
                    const etek_eni = parseFloat(m.etek_eni || 60);
                    const area_front = ((gogus + etek_eni) / 2.0) * boy * 1.15 / 10000.0;
                    const area_back = ((gogus + etek_eni) / 2.0) * boy * 1.15 / 10000.0;
                    const area_kol = kol_boyu > 0 ? 2.0 * kol_boyu * 20.0 * 1.15 / 10000.0 : 0;
                    const area_detay = 0.04;
                    netArea = area_front + area_back + area_kol + area_detay;
                } else if (urunGrubu.includes("tulum")) {
                    const gogus = parseFloat(m.gogus || 48);
                    const basen = parseFloat(m.basen || 85);
                    const boy = parseFloat(m.boy || 120);
                    const ic_ag = parseFloat(m.ic_ag || 65);
                    const kol_boyu = parseFloat(m.kol_boyu || 0);
                    const paca_eni = parseFloat(m.paca_eni || 22);
                    const area_upper = gogus * (boy - ic_ag) * 2.0 * 1.15 / 10000.0;
                    const area_lower = 2.0 * ((basen / 2.0 + paca_eni) / 2.0) * ic_ag * 1.15 / 10000.0;
                    const area_kol = kol_boyu > 0 ? 2.0 * kol_boyu * 20.0 * 1.15 / 10000.0 : 0;
                    const area_detay = 0.05;
                    netArea = area_upper + area_lower + area_kol + area_detay;
                }
                
                const qty = asortiData[size] || 0;
                totalNetArea += netArea * qty;
                netAreasList.push(netArea);
                labels.push(size);
            });
            
            valNetMetraj.innerText = `${totalNetArea.toFixed(3)} m²`;
            updateChart(labels, netAreasList);
        }
    }, 200);
    
    showSystemMessage(`Geçmiş çalışma (#${study.Calisma_ID}) forma başarıyla yüklendi.`, "success");
}

// -------------------------------------------------------------------------
// ADD NEW ENTRIES (MODALS)
// -------------------------------------------------------------------------

async function handleAddModel(e) {
    const modelData = {
        model_adi: document.getElementById("newModelName").value,
        urun_grubu: document.getElementById("newModelGroup").value
    };
    
    try {
        const res = await fetch(`${API_BASE}/api/modeller`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(modelData)
        });
        const result = await res.json();
        if (result.success) {
            modelModal.style.display = "none";
            modelForm.reset();
            await loadModeller(result.model_id);
            showSystemMessage(`"${modelData.model_adi}" modeli sisteme eklendi ve seçildi.`, "success");
        } else {
            alert("Model eklenemedi: " + result.error);
        }
    } catch (err) {
        console.error("Error adding model: ", err);
    }
}

async function handleDeleteModel() {
    const modelId = modelSelect.value;
    if (!modelId) {
        alert("Lütfen önce silmek istediğiniz modeli seçin.");
        return;
    }
    
    const selectedText = modelSelect.options[modelSelect.selectedIndex].text;
    if (!confirm(`"${selectedText}" modelini ve bu modele ait tüm geçmiş çalışmaları veri tabanından silmek istediğinize emin misiniz? Bu işlem geri alınamaz.`)) {
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/modeller/delete`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ model_id: parseInt(modelId) })
        });
        const result = await res.json();
        if (result.success) {
            showSystemMessage(`"${selectedText}" modeli ve ilişkili tüm çalışmalar başarıyla silindi.`, "success");
            clearForm();
            await loadModeller();
            await loadHistory();
        } else {
            alert("Model silinirken hata oluştu: " + result.error);
        }
    } catch (err) {
        console.error("Error deleting model: ", err);
        alert("Bağlantı hatası oluştu.");
    }
}

// -------------------------------------------------------------------------
// MATHEMATICAL CALCULATION ENGINE INITIATION
// -------------------------------------------------------------------------

async function handleCalculate() {
    const model_id = modelSelect.value;
    
    if (!model_id) {
        alert("Lütfen önce Model seçimi yapın.");
        return;
    }
    
    const asorti = {};
    const asortiInputs = asortiContainer.querySelectorAll(".asorti-val-input");
    let totalAsortiCount = 0;
    
    asortiInputs.forEach(inp => {
        const size = inp.getAttribute("data-size");
        const val = parseInt(inp.value) || 0;
        if (val > 0) {
            asorti[size] = val;
            totalAsortiCount += val;
        }
    });
    
    if (totalAsortiCount === 0) {
        alert("Lütfen en az bir beden için asorti miktarı (oranı) girin.");
        return;
    }
    
    const olculer = getMeasurementsValues();
    
    // AI Eğitim - Check for corrections
    if (lastParsedData && lastParsedData.olculer) {
        let diffs = [];
        const sizes = new Set([...Object.keys(lastParsedData.olculer || {}), ...Object.keys(olculer || {})]);
        for (const size of sizes) {
            const pSize = lastParsedData.olculer[size] || {};
            const fSize = olculer[size] || {};
            const params = new Set([...Object.keys(pSize), ...Object.keys(fSize)]);
            for (const p of params) {
                const pVal = parseFloat(pSize[p]) || 0;
                const fVal = parseFloat(fSize[p]) || 0;
                if (pVal !== fVal) {
                    diffs.push({
                        beden: size,
                        olcu_adi: p,
                        hatali: pVal,
                        dogru: fVal
                    });
                }
            }
        }
        if (diffs.length > 0) {
            const hataliStr = diffs.map(d => `${d.beden} bedende ${d.olcu_adi}: ${d.hatali}`).join("\n");
            const dogruStr = diffs.map(d => `${d.beden} bedende ${d.olcu_adi}: ${d.dogru}`).join("\n");
            try {
                await fetch(`${API_BASE}/api/ogrenme`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        tip: "olcu_duzeltme",
                        hatalar: `Dosya: ${lastParsedFileName}\n${hataliStr}`,
                        dogrular: dogruStr
                    })
                });
                showSystemMessage("AI modelinizi geliştirmek için ölçü düzeltmeleri kaydedildi.", "success");
            } catch (e) {
                console.error("AI Eğitim veri gönderimi hatası:", e);
            }
            lastParsedData = null; // Do not send again for the same parse
        }
    }
    
    const data = {
        model_id: parseInt(model_id),
        kumas_eni_cm: parseInt(kumasEnInput.value || 175),
        cekme_en_yuzde: parseFloat(cekmeEnInput.value || 0.0),
        cekme_boy_yuzde: parseFloat(cekmeBoyInput.value || 0.0),
        verimlilik_yuzde: parseFloat(verimlilikInput.value || 90.0),
        asorti: asorti,
        olculer: olculer,
        cep_kumastan: cepKumastan.checked,
        astar_hesapla: astarHesapla.checked,
        astar_eni_cm: parseInt(astarEnInput.value || 140),
        astar_cekme_en_yuzde: parseFloat(astarCekmeEnInput.value || 0.0),
        astar_cekme_boy_yuzde: parseFloat(astarCekmeBoyInput.value || 0.0),
        tul_hesapla: tulHesapla.checked,
        tul_eni_cm: parseInt(tulEnInput.value || 150),
        tul_cekme_en_yuzde: parseFloat(tulCekmeEnInput.value || 0.0),
        tul_cekme_boy_yuzde: parseFloat(tulCekmeBoyInput.value || 0.0)
    };
    
    calculateBtn.disabled = true;
    calculateBtn.innerText = "Hesaplanıyor...";
    
    try {
        const res = await fetch(`${API_BASE}/api/calculate`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        if (result.success) {
            const results = result.results;
            
            animateValueUpdate(metricBirimTuketim, `${results.birim_metraj_m.toFixed(3)} m`);
            animateValueUpdate(metricPastalBoyu, `${results.pastal_boyu_m.toFixed(2)} m`);
            
            valNetMetraj.innerText = `${results.total_net_area_m2.toFixed(3)} m²`;
            valCekmeFaktoru.innerText = `${results.cekme_faktoru.toFixed(4)}`;
            valToplamAsorti.innerText = `${results.toplam_asorti_adet} Adet`;
            valVerimlilik.innerText = `%${results.verimlilik_yuzde.toFixed(1)}`;
            
            if (results.astar_birim_metraj_m > 0 || astarHesapla.checked) {
                valAstarBirimCard.style.display = "block";
                valAstarPastalCard.style.display = "block";
                valAstarBirim.innerText = `${results.astar_birim_metraj_m.toFixed(3)} m`;
                valAstarPastal.innerText = `${results.astar_pastal_boyu_m.toFixed(2)} m`;
            } else {
                valAstarBirimCard.style.display = "none";
                valAstarPastalCard.style.display = "none";
            }
            
            if (results.tul_birim_metraj_m > 0 || tulHesapla.checked) {
                valTulBirimCard.style.display = "block";
                valTulPastalCard.style.display = "block";
                valTulBirim.innerText = `${results.tul_birim_metraj_m.toFixed(3)} m`;
                valTulPastal.innerText = `${results.tul_pastal_boyu_m.toFixed(2)} m`;
            } else {
                valTulBirimCard.style.display = "none";
                valTulPastalCard.style.display = "none";
            }
            
            if (results.cep_birim_metraj_m > 0) {
                valCepBirimCard.style.display = "block";
                valCepPastalCard.style.display = "block";
                valCepBirim.innerText = `${results.cep_birim_metraj_m.toFixed(3)} m`;
                valCepPastal.innerText = `${results.cep_pastal_boyu_m.toFixed(2)} m`;
            } else {
                valCepBirimCard.style.display = "none";
                valCepPastalCard.style.display = "none";
            }
            
            const labels = Object.keys(results.net_areas);
            const values = Object.values(results.net_areas);
            updateChart(labels, values);
            
            let learningMsg = "";
            if (results.learning_samples_count && results.learning_samples_count > 0) {
                learningMsg += `🤖 <strong>Kumaş Öğrenme Katsayısı: x${results.correction_factor.toFixed(3)}</strong> (Geçmiş ${results.learning_samples_count} kumaş verisine göre)<br>`;
            }
            if (results.astar_learning_samples_count && results.astar_learning_samples_count > 0) {
                learningMsg += `🤖 <strong>Astar Öğrenme Katsayısı: x${results.astar_correction_factor.toFixed(3)}</strong> (Geçmiş ${results.astar_learning_samples_count} astar verisine göre)<br>`;
            }
            if (results.tul_learning_samples_count && results.tul_learning_samples_count > 0) {
                learningMsg += `🤖 <strong>Tül Öğrenme Katsayısı: x${results.tul_correction_factor.toFixed(3)}</strong> (Geçmiş ${results.tul_learning_samples_count} tül verisine göre)<br>`;
            }
            if (learningMsg) {
                appendBotMessage(learningMsg);
                showSystemMessage("Sapma analizi ve öğrenme katsayıları uygulandı.", "success");
            } else {
                showSystemMessage("Tüketim hesaplaması başarıyla tamamlandı ve SQLite veri tabanına kaydedildi.", "success");
            }
            loadHistory();
            feedbackPanel.style.display = "block";
            feedbackCalismaId.value = results.calisma_id;
            feedbackTuketim.value = "";
            
            if (data.astar_hesapla) {
                document.getElementById("feedbackAstarGroup").style.display = "block";
                feedbackAstarTuketim.value = "";
            } else {
                document.getElementById("feedbackAstarGroup").style.display = "none";
                feedbackAstarTuketim.value = "";
            }
            
            if (data.tul_hesapla) {
                document.getElementById("feedbackTulGroup").style.display = "block";
                feedbackTulTuketim.value = "";
            } else {
                document.getElementById("feedbackTulGroup").style.display = "none";
                feedbackTulTuketim.value = "";
            }
            
            feedbackKumasEni.value = data.kumas_eni_cm;
            feedbackCekmeEn.value = data.cekme_en_yuzde;
            feedbackCekmeBoy.value = data.cekme_boy_yuzde;
            
            renderFeedbackAsortiGrid({
                Asorti_JSON: JSON.stringify(data.asorti),
                Gerceklesen_Asorti_JSON: ""
            });
        } else {
            alert("Hesaplama hatası: " + result.error);
        }
    } catch (e) {
        console.error("Calculation fetch error: ", e);
        alert("Hesaplama servisine bağlanılamadı.");
    } finally {
        calculateBtn.disabled = false;
        calculateBtn.innerText = "Hesapla ve Kaydet";
    }
}

function animateValueUpdate(element, newValue) {
    element.style.opacity = 0;
    setTimeout(() => {
        element.innerText = newValue;
        element.style.opacity = 1;
    }, 150);
}

function clearForm() {
    kumasEnInput.value = "175";
    modelSelect.value = "";
    cekmeEnInput.value = "0.00";
    cekmeBoyInput.value = "0.00";
    
    cepKumastan.checked = true;
    
    sizeGroupSelect.value = "adult";
    renderAsortiInputs("adult");
    
    metricBirimTuketim.innerText = "0.00 m";
    metricPastalBoyu.innerText = "0.00 m";
    valNetMetraj.innerText = "0.00 m²";
    valCekmeFaktoru.innerText = "1.000";
    valToplamAsorti.innerText = "0 Adet";
    valVerimlilik.innerText = "%90.0";
    
    astarHesapla.checked = false;
    astarInputsContainer.style.display = "none";
    astarEnInput.value = "140";
    astarCekmeEnInput.value = "0.00";
    astarCekmeBoyInput.value = "0.00";
    valAstarBirimCard.style.display = "none";
    valAstarPastalCard.style.display = "none";
    valAstarBirim.innerText = "0.00 m";
    valAstarPastal.innerText = "0.00 m";
    
    tulHesapla.checked = false;
    tulInputsContainer.style.display = "none";
    tulEnInput.value = "150";
    tulCekmeEnInput.value = "0.00";
    tulCekmeBoyInput.value = "0.00";
    valTulBirimCard.style.display = "none";
    valTulPastalCard.style.display = "none";
    valTulBirim.innerText = "0.00 m";
    valTulPastal.innerText = "0.00 m";
    
    valCepBirimCard.style.display = "none";
    valCepPastalCard.style.display = "none";
    valCepBirim.innerText = "0.00 m";
    valCepPastal.innerText = "0.00 m";
    
    feedbackPanel.style.display = "none";
    feedbackCalismaId.value = "";
    feedbackTuketim.value = "";
    feedbackKumasEni.value = "";
    feedbackCekmeEn.value = "";
    feedbackCekmeBoy.value = "";
    document.getElementById("feedbackAsortiGrid").innerHTML = "";
    document.getElementById("feedbackAsortiContainer").style.display = "none";
    
    updateChart([], []);
    showSystemMessage("Form temizlendi.", "info");
}

// -------------------------------------------------------------------------
// DOCK CHATBOT INTEGRATION
// -------------------------------------------------------------------------

function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text && !stagedFile) return;
    
    if (stagedFile) {
        let msg = `Dosya gönderildi: 📄 <strong>${stagedFile.name}</strong>`;
        if (text) {
            msg += `<br><br>${text}`;
        }
        appendUserMessage(msg);
        chatInput.value = "";
        
        const typingDiv = document.createElement("div");
        typingDiv.className = "message bot-message typing-indicator-msg";
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        parseFileWithUserText(stagedFile, text, typingDiv);
        clearStagedFile();
    } else {
        appendUserMessage(text);
        chatInput.value = "";
        
        const typingDiv = document.createElement("div");
        typingDiv.className = "message bot-message typing-indicator-msg";
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        parseUserIntent(text, typingDiv);
    }
}

async function selectOrCreateModel(modelName, urunGrubu) {
    if (!modelName || !urunGrubu) return null;
    
    let existingModel = modeller.find(m => 
        m.Model_Adi.toLowerCase() === modelName.toLowerCase() ||
        m.Model_Adi.toLowerCase().includes(modelName.toLowerCase()) ||
        modelName.toLowerCase().includes(m.Model_Adi.toLowerCase())
    );
    
    if (existingModel) {
        modelSelect.value = existingModel.Model_ID;
        resetMeasurementKeysForGroup(existingModel.Urun_Grubu);
        renderMeasurementsTable();
        return `Model Seçildi: <strong>${existingModel.Model_Adi} (${existingModel.Urun_Grubu})</strong>`;
    } else {
        try {
            const addRes = await fetch(`${API_BASE}/api/modeller`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ model_adi: modelName, urun_grubu: urunGrubu })
            });
            const addResult = await addRes.json();
            if (addResult.success) {
                await loadModeller(addResult.model_id);
                return `Yeni Model Tanımlandı ve Seçildi: <strong>${modelName} (${urunGrubu})</strong>`;
            }
        } catch (err) {
            console.error("Error auto-creating model: ", err);
        }
    }
    return null;
}

function fillAstarAndTulAndVerimlilik(parsedData, fillSummary) {
    if (parsedData.verimlilik_yuzde !== undefined && parsedData.verimlilik_yuzde !== null) {
        verimlilikInput.value = parsedData.verimlilik_yuzde;
        fillSummary.push(`Hedef Verimlilik: <strong>%${parsedData.verimlilik_yuzde}</strong>`);
    }
    
    if (parsedData.astar_hesapla !== undefined && parsedData.astar_hesapla) {
        astarHesapla.checked = true;
        astarInputsContainer.style.display = "block";
        fillSummary.push(`Astar hesaplaması aktif edildi.`);
        if (parsedData.astar_eni_cm) {
            astarEnInput.value = parsedData.astar_eni_cm;
            fillSummary.push(`Astar Kumaş Eni: <strong>${parsedData.astar_eni_cm} cm</strong>`);
        }
        if (parsedData.astar_cekme_en_yuzde !== undefined && parsedData.astar_cekme_en_yuzde !== null) {
            astarCekmeEnInput.value = parsedData.astar_cekme_en_yuzde;
            fillSummary.push(`Astar Çekme En: <strong>%${parsedData.astar_cekme_en_yuzde}</strong>`);
        }
        if (parsedData.astar_cekme_boy_yuzde !== undefined && parsedData.astar_cekme_boy_yuzde !== null) {
            astarCekmeBoyInput.value = parsedData.astar_cekme_boy_yuzde;
            fillSummary.push(`Astar Çekme Boy: <strong>%${parsedData.astar_cekme_boy_yuzde}</strong>`);
        }
    }
    
    if (parsedData.tul_hesapla !== undefined && parsedData.tul_hesapla) {
        tulHesapla.checked = true;
        tulInputsContainer.style.display = "block";
        fillSummary.push(`Tül hesaplaması aktif edildi.`);
        if (parsedData.tul_eni_cm) {
            tulEnInput.value = parsedData.tul_eni_cm;
            fillSummary.push(`Tül Kumaş Eni: <strong>${parsedData.tul_eni_cm} cm</strong>`);
        }
        if (parsedData.tul_cekme_en_yuzde !== undefined && parsedData.tul_cekme_en_yuzde !== null) {
            tulCekmeEnInput.value = parsedData.tul_cekme_en_yuzde;
            fillSummary.push(`Tül Çekme En: <strong>%${parsedData.tul_cekme_en_yuzde}</strong>`);
        }
        if (parsedData.tul_cekme_boy_yuzde !== undefined && parsedData.tul_cekme_boy_yuzde !== null) {
            tulCekmeBoyInput.value = parsedData.tul_cekme_boy_yuzde;
            fillSummary.push(`Tül Çekme Boy: <strong>%${parsedData.tul_cekme_boy_yuzde}</strong>`);
        }
    }
}

async function parseUserIntent(text, typingDiv) {
    try {
        const res = await fetch(`${API_BASE}/api/chat/parse`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ text })
        });
        const parsedData = await res.json();
        
        lastParsedData = parsedData;
        lastParsedFileName = "Sesli/Metin Giriş";

        if (typingDiv && typingDiv.parentNode) {
            typingDiv.parentNode.removeChild(typingDiv);
        }
        
        if (parsedData.error) {
            if (parsedData.error.includes("rate limit") || parsedData.error.includes("quota")) {
                appendBotMessage(`⚠️ <strong>Yapay zeka servisi şu anda meşgul veya kota limitine ulaşıldı (HTTP 429).</strong> Lütfen 1 dakika bekleyip tekrar deneyiniz.`);
                showSystemMessage("Yapay zeka servis kotası aşıldı.", "error");
            } else {
                appendBotMessage(`⚠️ <strong>Girdiniz işlenirken bir hata oluştu:</strong> ${parsedData.error}`);
                showSystemMessage("Analiz hatası.", "error");
            }
            return;
        }
        
        let fillSummary = [];
        
        if (parsedData.model_adi && parsedData.urun_grubu) {
            const modelMsg = await selectOrCreateModel(parsedData.model_adi, parsedData.urun_grubu);
            if (modelMsg) fillSummary.push(modelMsg);
        }
        
        if (parsedData.kumas_eni_cm) {
            kumasEnInput.value = parsedData.kumas_eni_cm;
            fillSummary.push(`Kumaş Eni: <strong>${parsedData.kumas_eni_cm} cm</strong>`);
        }
        
        if (parsedData.cekme_en_yuzde !== undefined && parsedData.cekme_en_yuzde !== null && parsedData.cekme_en_yuzde !== 0.0) {
            cekmeEnInput.value = parsedData.cekme_en_yuzde;
            fillSummary.push(`Çekme En: <strong>%${parsedData.cekme_en_yuzde}</strong>`);
        }
        if (parsedData.cekme_boy_yuzde !== undefined && parsedData.cekme_boy_yuzde !== null && parsedData.cekme_boy_yuzde !== 0.0) {
            cekmeBoyInput.value = parsedData.cekme_boy_yuzde;
            fillSummary.push(`Çekme Boy: <strong>%${parsedData.cekme_boy_yuzde}</strong>`);
        }
        
        fillAstarAndTulAndVerimlilik(parsedData, fillSummary);
        
        let asortiData = parsedData.asorti || {};
        const sizesInOlculer = parsedData.olculer ? Object.keys(parsedData.olculer) : [];
        if (Object.keys(asortiData).length === 0 && sizesInOlculer.length > 0) {
            sizesInOlculer.forEach(sz => {
                asortiData[sz] = 0;
            });
        }
        
        if (Object.keys(asortiData).length > 0) {
            const keys = Object.keys(asortiData);
            const isAdult = keys.every(k => SIZE_GROUPS.adult.includes(k));
            const isChild1 = keys.every(k => SIZE_GROUPS.child1.includes(k));
            const isChild2 = keys.every(k => SIZE_GROUPS.child2.includes(k));
            
            let matchedGroup = "custom";
            if (isAdult) matchedGroup = "adult";
            else if (isChild1) matchedGroup = "child1";
            else if (isChild2) matchedGroup = "child2";
            
            sizeGroupSelect.value = matchedGroup;
            renderAsortiInputs(matchedGroup, asortiData);
            
            fillSummary.push(`Bedenler aktif edildi: <strong>${keys.join(", ")}</strong>`);
        }
        
        if (parsedData.olculer && Object.keys(parsedData.olculer).length > 0) {
            const olculerData = normalizeOlculer(parsedData.olculer);
            const modelId = modelSelect.value;
            const model = modeller.find(m => m.Model_ID == modelId);
            if (model) {
                resetMeasurementKeysForGroup(model.Urun_Grubu);
            }
            mergeMeasurementKeys(olculerData);
            renderMeasurementsTable(olculerData);
            fillSummary.push(`Beden ölçüleri tablosu otomatik güncellendi.`);
        }
        
        if (fillSummary.length > 0) {
            const respMsg = `İfadenizden şu bilgileri ayıkladım ve forma yerleştirdim:<br><br>${fillSummary.join("<br>")}<br><br>Gerekli düzenlemeleri yapıp, <strong>asorti miktarlarını ve çekme en/boy oranlarını girdikten sonra</strong> "Hesapla ve Kaydet" butonuna basabilirsiniz.`;
            appendBotMessage(respMsg);
            showSystemMessage("Form verileri yapay zeka tarafından dolduruldu.", "success");
        } else {
            appendBotMessage("İfadenizden form parametreleri çıkaramadım. Lütfen kumaş eni, çekme yüzdesi (%5 en, %3 boy gibi) ve beden oranları (asorti 1-2-2-1 gibi) belirtin.");
        }
        
    } catch (e) {
        console.error("AI Parse error: ", e);
        if (typingDiv && typingDiv.parentNode) {
            typingDiv.parentNode.removeChild(typingDiv);
        }
        appendBotMessage("Üzgünüm, ifadenizi işlerken bir sunucu hatasıyla karşılaştım.");
    }
}

function appendUserMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message user-message";
    msgDiv.innerHTML = `
        <div class="message-content"><p>${text}</p></div>
        <span class="message-time">${getCurrentTime()}</span>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendBotMessage(htmlContent) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-message";
    msgDiv.innerHTML = `
        <div class="message-content"><p>${htmlContent}</p></div>
        <span class="message-time">${getCurrentTime()}</span>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showSystemMessage(text, type = "info") {
    const statusText = document.getElementById("statusText");
    const colors = {
        success: "#10b981",
        error: "#ef4444",
        info: "#6366f1"
    };
    
    statusText.innerText = text;
    statusText.style.color = colors[type] || "#ffffff";
    setTimeout(() => {
        statusText.innerText = "Sistem Çevrimiçi - Hazır";
        statusText.style.color = "";
    }, 4500);
}

// -------------------------------------------------------------------------
// WEB SPEECH VOICE RECOGNITION SETUP
// -------------------------------------------------------------------------

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Speech recognition not supported in this browser.");
        voiceBtn.style.display = "none";
        return;
    }
    
    recognition = new SpeechRecognition();
    recognition.lang = "tr-TR";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    recognition.onstart = () => {
        isListening = true;
        voiceBtn.classList.add("listening");
        chatInput.placeholder = "Dinleniyor, lütfen konuşun...";
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        chatInput.value = transcript;
    };
    
    recognition.onerror = (event) => {
        console.error("Speech Recognition Error: ", event.error);
        showSystemMessage("Ses kaydı hatası: " + event.error, "error");
        stopListening();
    };
    
    recognition.onend = () => {
        stopListening();
        if (chatInput.value.trim() !== "") {
            handleSendMessage();
        }
    };
    
    voiceBtn.addEventListener("click", () => {
        if (isListening) {
            recognition.stop();
        } else {
            chatInput.value = "";
            recognition.start();
        }
    });
}

function stopListening() {
    isListening = false;
    voiceBtn.classList.remove("listening");
    chatInput.placeholder = "Mesajınızı yazın veya konuşun...";
}

// -------------------------------------------------------------------------
// CHART.JS INTEGRATION
// -------------------------------------------------------------------------

function initChart(labels = [], data = []) {
    const ctx = document.getElementById('costChart').getContext('2d');
    
    costChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Net Kalıp Alanı (m²)',
                data: data,
                backgroundColor: 'rgba(99, 102, 241, 0.65)',
                borderColor: '#6366f1',
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Kalıp Alanı: ${context.parsed.y.toFixed(4)} m²`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

function updateChart(labels = [], data = []) {
    if (!costChartInstance) return;
    
    costChartInstance.data.labels = labels;
    costChartInstance.data.datasets[0].data = data;
    costChartInstance.update();
}

// -------------------------------------------------------------------------
// FILE UPLOAD AND GEMINI ANALYSIS
// -------------------------------------------------------------------------

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    fileInput.value = "";
    
    const reader = new FileReader();
    reader.onload = function() {
        try {
            const dataUrl = reader.result;
            const base64Data = dataUrl.split(",")[1];
            const mimeType = file.type || "application/pdf";
            
            stagedFile = {
                name: file.name,
                base64: base64Data,
                mime: mimeType
            };
            
            renderAttachmentPreview();
        } catch (err) {
            console.error("File read error: ", err);
            showSystemMessage("Dosya okunurken hata oluştu.", "error");
        }
    };
    reader.readAsDataURL(file);
}

function renderAttachmentPreview() {
    const area = document.getElementById("attachmentArea");
    if (!area) return;
    
    if (stagedFile) {
        area.style.display = "flex";
        area.innerHTML = `
            <div class="attachment-chip" style="background: rgba(99, 102, 241, 0.15); border: 1px solid var(--color-primary); border-radius: 8px; padding: 6px 12px; display: inline-flex; align-items: center; gap: 8px; font-size: 0.85rem; width: fit-content; animation: slideIn 0.3s ease;">
                <span style="color: var(--text-main); display: flex; align-items: center; gap: 4px;">📄 <strong>${stagedFile.name}</strong></span>
                <span class="remove-attachment" style="cursor: pointer; font-weight: bold; color: var(--color-accent); font-size: 1.1rem; padding: 0 4px; transition: var(--transition-smooth);" title="Dosyayı kaldır" onmouseover="this.style.transform='scale(1.2)';" onmouseout="this.style.transform='scale(1)';">×</span>
            </div>
        `;
        
        area.querySelector(".remove-attachment").addEventListener("click", clearStagedFile);
        chatInput.placeholder = "PDF ile birlikte göndermek istediğiniz notları yazın...";
        chatInput.focus();
    } else {
        area.style.display = "none";
        area.innerHTML = "";
        chatInput.placeholder = "Mesajınızı yazın veya konuşun...";
    }
}

function clearStagedFile() {
    stagedFile = null;
    renderAttachmentPreview();
}

async function parseFileWithUserText(fileObj, userText, typingDiv) {
    try {
        const payload = {
            file_b64: fileObj.base64,
            mime_type: fileObj.mime,
            user_text: userText
        };
        
        showSystemMessage("Föy inceleniyor...", "info");
        
        const res = await fetch(`${API_BASE}/api/chat/parse_file`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        const parsedData = await res.json();
        
        // Save for AI Training comparison later
        lastParsedData = parsedData;
        lastParsedFileName = fileObj.name;
        
        if (typingDiv && typingDiv.parentNode) {
            typingDiv.parentNode.removeChild(typingDiv);
        }
        
        if (parsedData.error) {
            if (parsedData.error.includes("rate limit") || parsedData.error.includes("quota")) {
                appendBotMessage(`⚠️ <strong>Yapay zeka servisi şu anda meşgul veya kota limitine ulaşıldı (HTTP 429).</strong> Lütfen 1 dakika bekleyip tekrar deneyiniz.`);
                showSystemMessage("Yapay zeka servis kotası aşıldı.", "error");
            } else {
                appendBotMessage(`⚠️ <strong>Dosya analiz edilirken bir hata oluştu:</strong> ${parsedData.error}`);
                showSystemMessage("Dosya analiz hatası.", "error");
            }
            return;
        }
        
        let fillSummary = [];
        
        if (parsedData.model_adi && parsedData.urun_grubu) {
            const modelMsg = await selectOrCreateModel(parsedData.model_adi, parsedData.urun_grubu);
            if (modelMsg) fillSummary.push(modelMsg);
        }
        
        if (parsedData.kumas_eni_cm) {
            kumasEnInput.value = parsedData.kumas_eni_cm;
            fillSummary.push(`Kumaş Eni: <strong>${parsedData.kumas_eni_cm} cm</strong>`);
        }
        
        if (parsedData.cekme_en_yuzde !== undefined && parsedData.cekme_en_yuzde !== null) {
            cekmeEnInput.value = parsedData.cekme_en_yuzde;
            fillSummary.push(`Çekme En: <strong>%${parsedData.cekme_en_yuzde}</strong>`);
        }
        if (parsedData.cekme_boy_yuzde !== undefined && parsedData.cekme_boy_yuzde !== null) {
            cekmeBoyInput.value = parsedData.cekme_boy_yuzde;
            fillSummary.push(`Çekme Boy: <strong>%${parsedData.cekme_boy_yuzde}</strong>`);
        }
        
        fillAstarAndTulAndVerimlilik(parsedData, fillSummary);
        
        let asortiData = parsedData.asorti || {};
        const sizesInOlculer = parsedData.olculer ? Object.keys(parsedData.olculer) : [];
        if (Object.keys(asortiData).length === 0 && sizesInOlculer.length > 0) {
            sizesInOlculer.forEach(sz => {
                asortiData[sz] = 0;
            });
        }
        
        if (Object.keys(asortiData).length > 0) {
            const keys = Object.keys(asortiData);
            const isAdult = keys.every(k => SIZE_GROUPS.adult.includes(k));
            const isChild1 = keys.every(k => SIZE_GROUPS.child1.includes(k));
            const isChild2 = keys.every(k => SIZE_GROUPS.child2.includes(k));
            
            let matchedGroup = "custom";
            if (isAdult) matchedGroup = "adult";
            else if (isChild1) matchedGroup = "child1";
            else if (isChild2) matchedGroup = "child2";
            
            sizeGroupSelect.value = matchedGroup;
            renderAsortiInputs(matchedGroup, asortiData);
            
            fillSummary.push(`Bedenler aktif edildi: <strong>${keys.join(", ")}</strong>`);
        }
        
        if (parsedData.olculer && Object.keys(parsedData.olculer).length > 0) {
            const olculerData = normalizeOlculer(parsedData.olculer);
            const modelId = modelSelect.value;
            const model = modeller.find(m => m.Model_ID == modelId);
            if (model) {
                resetMeasurementKeysForGroup(model.Urun_Grubu);
            }
            mergeMeasurementKeys(olculerData);
            renderMeasurementsTable(olculerData);
            fillSummary.push(`Beden ölçüleri tablosu otomatik dolduruldu.`);
        }
        
        if (fillSummary.length > 0) {
            const respMsg = `Yüklediğiniz 📄 <strong>${fileObj.name}</strong> föyünden ve notlarınızdan şu bilgileri ayıkladım ve forma yerleştirdim:<br><br>${fillSummary.join("<br>")}<br><br>Gerekli alanları inceleyip, <strong>lütfen kendi asorti miktarlarınızı ve çekme en/boy oranlarınızı girdikten sonra</strong> 'Hesapla ve Kaydet' butonuna basarak mikro tüketim hesaplamasını başlatabilirsiniz.`;
            appendBotMessage(respMsg);
            showSystemMessage("Teknik föy verileri başarıyla yüklendi.", "success");
        } else {
            appendBotMessage(`📄 <strong>${fileObj.name}</strong> dosyası analiz edildi, ancak form için anlamlı parametreler bulunamadı. Lütfen bilgileri kontrol edin.`);
        }
        
    } catch (err) {
        console.error("File parse error: ", err);
        if (typingDiv && typingDiv.parentNode) {
            typingDiv.parentNode.removeChild(typingDiv);
        }
        appendBotMessage("Dosya analiz edilirken sunucu tarafında bir hata oluştu.");
        showSystemMessage("Dosya analiz hatası.", "error");
    }
}

// -------------------------------------------------------------------------
// FEEDBACK: SAVE REALIZED VALUES
// -------------------------------------------------------------------------

async function handleSaveFeedback() {
    const calisma_id = feedbackCalismaId.value;
    const tuketim = feedbackTuketim.value.trim();
    const astarTuketim = feedbackAstarTuketim.value.trim();
    const tulTuketim = feedbackTulTuketim.value.trim();
    
    if (!calisma_id) {
        alert("Lütfen önce geçmişten bir çalışma seçin.");
        return;
    }
    
    saveFeedbackBtn.disabled = true;
    saveFeedbackBtn.innerText = "Kaydediliyor ve Yapay Zeka Eğitiliyor...";
    
    const asortiInputs = document.querySelectorAll(".feedback-asorti-input");
    const gerceklesen_asorti = {};
    asortiInputs.forEach(input => {
        const size = input.getAttribute("data-size");
        const val = parseInt(input.value) || 0;
        gerceklesen_asorti[size] = val;
    });

    const realizedKumasEni = feedbackKumasEni.value.trim();
    const realizedCekmeEn = feedbackCekmeEn.value.trim();
    const realizedCekmeBoy = feedbackCekmeBoy.value.trim();

    try {
        const payload = {
            calisma_id: parseInt(calisma_id),
            gerceklesen_tuketim: tuketim !== "" ? parseFloat(tuketim) : null,
            gerceklesen_astar_tuketim: astarTuketim !== "" ? parseFloat(astarTuketim) : null,
            gerceklesen_tul_tuketim: tulTuketim !== "" ? parseFloat(tulTuketim) : null,
            gerceklesen_asorti: gerceklesen_asorti,
            gerceklesen_kumas_eni: realizedKumasEni !== "" ? parseInt(realizedKumasEni) : null,
            gerceklesen_cekme_en: realizedCekmeEn !== "" ? parseFloat(realizedCekmeEn) : null,
            gerceklesen_cekme_boy: realizedCekmeBoy !== "" ? parseFloat(realizedCekmeBoy) : null
        };
        
        const res = await fetch(`${API_BASE}/api/calismalar/feedback`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.success) {
            showSystemMessage("Gerçekleşen üretim verileri kaydedildi. Yapay zeka bu verilerden öğreniyor.", "success");
            if (result.analysis) {
                appendBotMessage(result.analysis);
            }
            await loadHistory();
        } else {
            alert("Hata oluştu: " + result.error);
        }
    } catch (err) {
        console.error("Error saving realized values feedback:", err);
    } finally {
        saveFeedbackBtn.disabled = false;
        saveFeedbackBtn.innerText = "Gerçekleşen Verileri Kaydet ve Yapay Zekayı Eğit";
    }
}

async function handleClearFeedback() {
    const calisma_id = feedbackCalismaId.value;
    if (!calisma_id) {
        alert("Lütfen önce geçmişten bir çalışma seçin.");
        return;
    }
    
    if (!confirm("Bu çalışmaya ait öğrettiğiniz gerçekleşen üretim verilerini silmek istediğinize emin misiniz?")) {
        return;
    }
    
    clearFeedbackBtn.disabled = true;
    clearFeedbackBtn.innerText = "Siliniyor...";
    
    try {
        const res = await fetch(`${API_BASE}/api/calismalar/feedback/reset`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ calisma_id: parseInt(calisma_id) })
        });
        
        const result = await res.json();
        if (result.success) {
            showSystemMessage("Bu çalışmaya ait öğretilen üretim verileri başarıyla silindi.", "success");
            feedbackTuketim.value = "";
            feedbackAstarTuketim.value = "";
            feedbackTulTuketim.value = "";
            await loadHistory();
        } else {
            alert("Hata oluştu: " + result.error);
        }
    } catch (err) {
        console.error("Error clearing feedback:", err);
    } finally {
        clearFeedbackBtn.disabled = false;
        clearFeedbackBtn.innerText = "Öğretilenleri Sil";
    }
}

async function handleDeleteCalisma(calismaId) {
    if (!confirm("Bu çalışmayı veri tabanından tamamen silmek istediğinize emin misiniz? Bu işlem geri alınamaz.")) {
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/calismalar/delete`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ calisma_id: parseInt(calismaId) })
        });
        
        const result = await res.json();
        if (result.success) {
            showSystemMessage("Çalışma başarıyla veri tabanından silindi.", "success");
            if (feedbackCalismaId.value == calismaId) {
                clearForm();
            }
            await loadHistory();
        } else {
            alert("Hata oluştu: " + result.error);
        }
    } catch (err) {
        console.error("Error deleting calisma:", err);
    }
}
