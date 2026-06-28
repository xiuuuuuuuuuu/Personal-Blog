function shuffle<T>(items: T[]): T[] {
    const arr = [...items];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

class SchulteTable {
    private readonly root: HTMLElement;
    private readonly grid: HTMLElement;
    private readonly timerEl: HTMLElement;
    private readonly progressEl: HTMLElement;
    private readonly hintEl: HTMLElement;
    private readonly startBtn: HTMLButtonElement;
    private readonly resetBtn: HTMLButtonElement;
    private readonly size = 5;
    private current = 1;
    private startTime = 0;
    private timerId = 0;

    constructor(root: HTMLElement) {
        this.root = root;
        this.grid = root.querySelector(".schulte-table__grid")!;
        this.timerEl = root.querySelector(".schulte-table__timer")!;
        this.progressEl = root.querySelector(".schulte-table__progress")!;
        this.hintEl = root.querySelector(".schulte-table__hint")!;
        this.startBtn = root.querySelector(".schulte-table__start")!;
        this.resetBtn = root.querySelector(".schulte-table__reset")!;

        this.startBtn.addEventListener("click", () => this.startGame());
        this.resetBtn.addEventListener("click", () => this.reset());

        this.reset();
    }

    private updateProgress(): void {
        const total = this.size * this.size;
        if (this.current > total) {
            this.progressEl.textContent = "完成";
            return;
        }
        this.progressEl.textContent = `下一个: ${this.current}`;
    }

    private reset(): void {
        this.current = 1;
        this.stopTimer();
        this.timerEl.textContent = "--";
        this.progressEl.hidden = true;
        this.grid.innerHTML = "";
        this.grid.hidden = true;
        this.startBtn.hidden = false;
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
        this.startBtn.hidden = true;
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
        this.updateProgress();

        if (this.current > this.size * this.size) {
            this.stopTimer();
            this.root.className = "widget schulte-table schulte-table--finished";
            if (this.hintEl) {
                this.hintEl.textContent = "完成！点击 ↻ 再来一局";
            }
        }
    }
}

export function initSchulteTables(): void {
    document.querySelectorAll<HTMLElement>(".schulte-table").forEach((root) => {
        new SchulteTable(root);
    });
}
