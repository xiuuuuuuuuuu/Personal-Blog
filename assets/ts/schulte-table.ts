function shuffle<T>(items: T[]): T[] {
    const arr = [...items];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

interface SchulteRating {
    label: string;
    description: string;
}

function getRating(seconds: number): SchulteRating {
    if (seconds < 10) {
        return {
            label: "超凡反应",
            description: "顶尖水平，接近飞行员/电竞选手",
        };
    }
    if (seconds < 15) {
        return {
            label: "非常优秀",
            description: "注意力和搜索效率极好",
        };
    }
    if (seconds < 20) {
        return {
            label: "良好",
            description: "高于普通水平",
        };
    }
    if (seconds < 30) {
        return {
            label: "正常水平",
            description: "大部分成年人的范围",
        };
    }
    if (seconds < 40) {
        return {
            label: "需要放松",
            description: "略慢，可能注意力没集中",
        };
    }
    return {
        label: "试试再挑战一次",
        description: "不熟练或分心了，可以多练",
    };
}

class SchulteTable {
    private readonly root: HTMLElement;
    private readonly grid: HTMLElement;
    private readonly resultEl: HTMLElement;
    private readonly ratingEl: HTMLElement;
    private readonly descEl: HTMLElement;
    private readonly timerEl: HTMLElement;
    private readonly progressEl: HTMLElement;
    private readonly hintEl: HTMLElement;
    private readonly startBtn: HTMLButtonElement;
    private readonly resetBtn: HTMLButtonElement;
    private readonly restartBtn: HTMLButtonElement;
    private readonly size = 5;
    private current = 1;
    private startTime = 0;
    private timerId = 0;

    constructor(root: HTMLElement) {
        this.root = root;
        this.grid = root.querySelector(".schulte-table__grid")!;
        this.resultEl = root.querySelector(".schulte-table__result")!;
        this.ratingEl = root.querySelector(".schulte-table__result-rating")!;
        this.descEl = root.querySelector(".schulte-table__result-desc")!;
        this.timerEl = root.querySelector(".schulte-table__timer")!;
        this.progressEl = root.querySelector(".schulte-table__progress")!;
        this.hintEl = root.querySelector(".schulte-table__hint")!;
        this.startBtn = root.querySelector(".schulte-table__start")!;
        this.resetBtn = root.querySelector(".schulte-table__reset")!;
        this.restartBtn = root.querySelector(".schulte-table__restart")!;

        this.startBtn.addEventListener("click", () => this.startGame());
        this.resetBtn.addEventListener("click", () => this.reset());
        this.restartBtn.addEventListener("click", () => this.startGame());

        this.reset();
    }

    private updateProgress(): void {
        this.progressEl.textContent = `下一个: ${this.current}`;
    }

    private hideResult(): void {
        this.resultEl.hidden = true;
    }

    private reset(): void {
        this.current = 1;
        this.stopTimer();
        this.timerEl.textContent = "--";
        this.progressEl.hidden = true;
        this.grid.innerHTML = "";
        this.grid.hidden = true;
        this.hideResult();
        this.resetBtn.hidden = true;
        this.root.className = "widget schulte-table schulte-table--idle";

        if (this.hintEl) {
            this.hintEl.textContent = "按 1 → 25 顺序点击";
        }
    }

    private startGame(): void {
        this.current = 1;
        this.stopTimer();
        this.timerEl.textContent = "0.00s";
        this.progressEl.hidden = false;
        this.updateProgress();
        this.hideResult();
        this.resetBtn.hidden = false;
        this.root.className = "widget schulte-table schulte-table--playing";

        if (this.hintEl) {
            this.hintEl.textContent = "按 1 → 25 顺序点击";
        }

        const total = this.size * this.size;
        const numbers = shuffle(Array.from({ length: total }, (_, index) => index + 1));

        this.grid.innerHTML = "";
        this.grid.style.gridTemplateColumns = `repeat(${this.size}, 1fr)`;
        this.grid.hidden = false;

        numbers.forEach((value) => {
            const cell = document.createElement("button");
            cell.type = "button";
            cell.className = "schulte-table__cell";
            cell.textContent = String(value);
            cell.setAttribute("aria-label", `数字 ${value}`);
            cell.addEventListener("click", () => this.onCellClick(value, cell));
            this.grid.appendChild(cell);
        });

        this.startTime = Date.now();
        this.timerId = window.setInterval(() => {
            const elapsed = (Date.now() - this.startTime) / 1000;
            this.timerEl.textContent = `${elapsed.toFixed(2)}s`;
        }, 50);
    }

    private stopTimer(): void {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = 0;
        }
    }

    private finishGame(): void {
        this.stopTimer();
        const elapsed = (Date.now() - this.startTime) / 1000;
        this.timerEl.textContent = `${elapsed.toFixed(2)}s`;

        const rating = getRating(elapsed);
        this.ratingEl.textContent = rating.label;
        this.descEl.textContent = rating.description;

        this.grid.hidden = true;
        this.progressEl.hidden = true;
        this.resetBtn.hidden = true;
        this.resultEl.hidden = false;
        this.root.className = "widget schulte-table schulte-table--finished";

        if (this.hintEl) {
            this.hintEl.textContent = `${elapsed.toFixed(2)} 秒 · ${rating.label}`;
        }
    }

    private flashHit(cell: HTMLButtonElement): void {
        cell.classList.add("schulte-table__cell--hit");
        cell.addEventListener(
            "animationend",
            () => cell.classList.remove("schulte-table__cell--hit"),
            { once: true },
        );
    }

    private onCellClick(value: number, cell: HTMLButtonElement): void {
        if (value !== this.current) {
            cell.classList.add("schulte-table__cell--wrong");
            window.setTimeout(() => cell.classList.remove("schulte-table__cell--wrong"), 250);
            return;
        }

        this.flashHit(cell);
        cell.disabled = true;
        this.current += 1;

        if (this.current <= this.size * this.size) {
            this.updateProgress();
        }

        if (this.current > this.size * this.size) {
            this.finishGame();
        }
    }
}

export function initSchulteTables(): void {
    document.querySelectorAll<HTMLElement>(".schulte-table").forEach((root) => {
        new SchulteTable(root);
    });
}
