const state = {
    user: null,

    tokens: {
        accessToken: null,
        refreshToken: null,
    },

    games: [],
    genres: [],
    library: [],
    orders: [],
    notifications: [],
    services: {},

    page: "store",
    authMode: "login",
};


const elements = {
    pages: document.querySelectorAll(
        ".page"
    ),

    navButtons: document.querySelectorAll(
        ".nav-button"
    ),

    guestActions:
        document.querySelector(
            "#guestActions"
        ),

    userActions:
        document.querySelector(
            "#userActions"
        ),

    userEmail:
        document.querySelector(
            "#userEmail"
        ),

    userRole:
        document.querySelector(
            "#userRole"
        ),

    adminNav:
        document.querySelector(
            "#adminNav"
        ),

    notificationBadge:
        document.querySelector(
            "#notificationBadge"
        ),

    gamesGrid:
        document.querySelector(
            "#gamesGrid"
        ),

    gameSearch:
        document.querySelector(
            "#gameSearch"
        ),

    genreFilter:
        document.querySelector(
            "#genreFilter"
        ),

    libraryGrid:
        document.querySelector(
            "#libraryGrid"
        ),

    ordersContent:
        document.querySelector(
            "#ordersContent"
        ),

    notificationsList:
        document.querySelector(
            "#notificationsList"
        ),

    servicesGrid:
        document.querySelector(
            "#servicesGrid"
        ),

    heroStatusText:
        document.querySelector(
            "#heroStatusText"
        ),

    heroStatusDot:
        document.querySelector(
            ".hero-status .status-dot"
        ),

    authDialog:
        document.querySelector(
            "#authDialog"
        ),

    authTitle:
        document.querySelector(
            "#authTitle"
        ),

    authForm:
        document.querySelector(
            "#authForm"
        ),

    authEmail:
        document.querySelector(
            "#authEmail"
        ),

    authPassword:
        document.querySelector(
            "#authPassword"
        ),

    authSubmitButton:
        document.querySelector(
            "#authSubmitButton"
        ),

    authModeToggle:
        document.querySelector(
            "#authModeToggle"
        ),

    reviewsDialog:
        document.querySelector(
            "#reviewsDialog"
        ),

    reviewsTitle:
        document.querySelector(
            "#reviewsTitle"
        ),

    reviewsContent:
        document.querySelector(
            "#reviewsContent"
        ),

    toastContainer:
        document.querySelector(
            "#toastContainer"
        ),

    genreForm:
        document.querySelector(
            "#genreForm"
        ),

    genreName:
        document.querySelector(
            "#genreName"
        ),

    gameForm:
        document.querySelector(
            "#gameForm"
        ),

    gameGenres:
        document.querySelector(
            "#gameGenres"
        ),
};


class ApiError extends Error {

    constructor(
        message,
        status,
        payload,
    ) {
        super(message);

        this.status = status;
        this.payload = payload;
    }

}


function loadStoredSession() {

    const raw = localStorage.getItem(
        "gamehub-session"
    );

    if (!raw) {
        return;
    }

    try {

        const session = JSON.parse(
            raw
        );

        state.tokens.accessToken =
            session.accessToken
            || null;

        state.tokens.refreshToken =
            session.refreshToken
            || null;

    } catch {

        localStorage.removeItem(
            "gamehub-session"
        );

    }

}


function saveSession() {

    if (
        !state.tokens.accessToken
        || !state.tokens.refreshToken
    ) {

        localStorage.removeItem(
            "gamehub-session"
        );

        return;
    }

    localStorage.setItem(
        "gamehub-session",
        JSON.stringify({
            accessToken:
                state.tokens.accessToken,

            refreshToken:
                state.tokens.refreshToken,
        })
    );

}


function clearSession() {

    state.user = null;

    state.tokens.accessToken = null;
    state.tokens.refreshToken = null;

    state.library = [];
    state.orders = [];
    state.notifications = [];

    saveSession();

    updateAuthUi();
    renderStore();

}


async function parseResponse(
    response
) {

    if (
        response.status === 204
    ) {
        return null;
    }

    const contentType =
        response.headers.get(
            "content-type"
        )
        || "";

    if (
        contentType.includes(
            "application/json"
        )
    ) {

        return await response.json();

    }

    return await response.text();

}


function extractErrorMessage(
    payload,
    fallback,
) {

    if (!payload) {
        return fallback;
    }

    if (
        typeof payload === "string"
    ) {
        return payload;
    }

    const detail = payload.detail;

    if (
        typeof detail === "string"
    ) {
        return detail;
    }

    if (
        detail
        && typeof detail === "object"
    ) {

        return (
            detail.message
            || JSON.stringify(
                detail
            )
        );

    }

    return fallback;
}


async function refreshAccessToken() {

    if (
        !state.tokens.refreshToken
    ) {
        return false;
    }

    try {

        const response = await fetch(
            "/api/auth/refresh",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify({
                    refresh_token:
                        state.tokens
                            .refreshToken,
                }),
            }
        );

        if (!response.ok) {
            return false;
        }

        const payload =
            await response.json();

        state.tokens.accessToken =
            payload.access_token;

        state.tokens.refreshToken =
            payload.refresh_token;

        saveSession();

        return true;

    } catch {

        return false;

    }

}


async function apiRequest(
    path,
    options = {},
    retryAuth = true,
) {

    const headers = new Headers(
        options.headers || {}
    );

    if (
        options.body
        && !headers.has(
            "Content-Type"
        )
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    if (
        state.tokens.accessToken
    ) {

        headers.set(
            "Authorization",
            (
                "Bearer "
                + state.tokens
                    .accessToken
            )
        );

    }

    const response = await fetch(
        path,
        {
            ...options,
            headers,
        }
    );

    if (
        response.status === 401
        && retryAuth
        && state.tokens.refreshToken
    ) {

        const refreshed =
            await refreshAccessToken();

        if (refreshed) {

            return await apiRequest(
                path,
                options,
                false,
            );

        }

        clearSession();

    }

    const payload =
        await parseResponse(
            response
        );

    if (!response.ok) {

        throw new ApiError(
            extractErrorMessage(
                payload,
                (
                    "Request failed with "
                    + response.status
                ),
            ),
            response.status,
            payload,
        );

    }

    return {
        data: payload,
        response,
    };

}


function toast(
    message,
    type = "success",
    detail = "",
) {

    const node =
        document.createElement(
            "div"
        );

    node.className =
        `toast ${type}`;

    node.innerHTML = `
        <strong>
            ${escapeHtml(message)}
        </strong>

        ${
            detail
                ? `
                    <small>
                        ${escapeHtml(detail)}
                    </small>
                `
                : ""
        }
    `;

    elements.toastContainer
        .appendChild(
            node
        );

    setTimeout(
        () => {
            node.remove();
        },
        4500,
    );

}


function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


function formatMoney(
    value
) {

    return new Intl.NumberFormat(
        "en-US",
        {
            style: "currency",
            currency: "USD",
        }
    ).format(
        Number(value)
    );

}


function formatDate(
    value
) {

    if (!value) {
        return "—";
    }

    return new Intl.DateTimeFormat(
        "en",
        {
            dateStyle: "medium",
            timeStyle: "short",
        }
    ).format(
        new Date(value)
    );

}


function navigate(
    page
) {

    if (
        [
            "library",
            "orders",
            "notifications",
        ].includes(page)
        && !state.user
    ) {

        openAuth(
            "login"
        );

        return;
    }

    if (
        page === "admin"
        && state.user?.role
            !== "admin"
    ) {
        return;
    }

    state.page = page;

    elements.pages.forEach(
        element => {

            element.classList.toggle(
                "active",
                element.id
                    === `page-${page}`,
            );

        }
    );

    elements.navButtons.forEach(
        button => {

            button.classList.toggle(
                "active",
                button.dataset.page
                    === page,
            );

        }
    );

    if (page === "library") {
        loadLibrary();
    }

    if (page === "orders") {
        loadOrders();
    }

    if (
        page === "notifications"
    ) {
        loadNotifications();
    }

    if (page === "system") {
        loadServices();
    }

    if (page === "admin") {
        loadGenres();
    }

}


function updateAuthUi() {

    const authenticated =
        Boolean(
            state.user
        );

    elements.guestActions
        .classList.toggle(
            "hidden",
            authenticated,
        );

    elements.userActions
        .classList.toggle(
            "hidden",
            !authenticated,
        );

    document
        .querySelectorAll(
            ".auth-only"
        )
        .forEach(
            node => {

                node.classList.toggle(
                    "hidden",
                    !authenticated,
                );

            }
        );

    if (authenticated) {

        elements.userEmail
            .textContent =
            state.user.email;

        elements.userRole
            .textContent =
            state.user.role;

    }

    elements.adminNav
        .classList.toggle(
            "hidden",
            (
                state.user?.role
                !== "admin"
            ),
        );

}


function openAuth(
    mode
) {

    state.authMode = mode;

    const register =
        mode === "register";

    elements.authTitle
        .textContent =
        register
            ? "Create account"
            : "Sign in";

    elements.authSubmitButton
        .textContent =
        register
            ? "Create account"
            : "Sign in";

    elements.authModeToggle
        .textContent =
        register
            ? (
                "Already have an "
                + "account? Sign in."
            )
            : (
                "Need an account? "
                + "Create one."
            );

    elements.authForm.reset();

    elements.authDialog
        .showModal();

}


async function handleAuthSubmit(
    event
) {

    event.preventDefault();

    const email =
        elements.authEmail
            .value
            .trim();

    const password =
        elements.authPassword
            .value;

    try {

        const endpoint =
            state.authMode
                === "register"
                ? "/api/auth/register"
                : "/api/auth/login";

        const {
            data,
        } = await apiRequest(
            endpoint,
            {
                method: "POST",

                body: JSON.stringify({
                    email,
                    password,
                }),
            },
            false,
        );

        state.user = data.user;

        state.tokens.accessToken =
            data.tokens
                .access_token;

        state.tokens.refreshToken =
            data.tokens
                .refresh_token;

        saveSession();

        updateAuthUi();

        elements.authDialog
            .close();

        await loadUserData();

        toast(
            (
                state.authMode
                === "register"
            )
                ? "Account created"
                : "Signed in",
            "success",
            state.user.email,
        );

    } catch (error) {

        toast(
            "Authentication failed",
            "error",
            error.message,
        );

    }

}


async function restoreUser() {

    if (
        !state.tokens.accessToken
    ) {

        updateAuthUi();

        return;
    }

    try {

        const {
            data,
        } = await apiRequest(
            "/api/auth/me"
        );

        state.user = data;

        updateAuthUi();

        await loadUserData();

    } catch {

        clearSession();

    }

}


async function loadUserData() {

    if (!state.user) {
        return;
    }

    await Promise.all([
        loadLibrary(false),
        loadOrders(false),
        loadNotifications(false),
    ]);

    renderStore();

}


async function loadGames() {

    try {

        const {
            data,
        } = await apiRequest(
            (
                "/api/games"
                + "?published=true"
                + "&limit=100"
            )
        );

        state.games = data;

        renderStore();

    } catch (error) {

        toast(
            "Cannot load catalog",
            "error",
            error.message,
        );

    }

}


async function loadGenres() {

    try {

        const {
            data,
        } = await apiRequest(
            "/api/genres"
        );

        state.genres = data;

        renderGenreControls();

    } catch (error) {

        toast(
            "Cannot load genres",
            "error",
            error.message,
        );

    }

}


function renderGenreControls() {

    const current =
        elements.genreFilter.value;

    elements.genreFilter.innerHTML =
        `
            <option value="">
                All genres
            </option>
        `
        + state.genres
            .map(
                genre => `
                    <option
                        value="${
                            escapeHtml(
                                genre.slug
                            )
                        }"
                    >
                        ${
                            escapeHtml(
                                genre.name
                            )
                        }
                    </option>
                `
            )
            .join("");

    elements.genreFilter.value =
        current;

    elements.gameGenres.innerHTML =
        state.genres
            .map(
                genre => `
                    <option
                        value="${genre.id}"
                    >
                        ${
                            escapeHtml(
                                genre.name
                            )
                        }
                    </option>
                `
            )
            .join("");

}


function ownedGameIds() {

    return new Set(
        state.library.map(
            item => item.game_id
        )
    );

}


function renderStore() {

    const search =
        elements.gameSearch
            .value
            .trim()
            .toLowerCase();

    const genre =
        elements.genreFilter
            .value;

    const owned =
        ownedGameIds();

    const games =
        state.games.filter(
            game => {

                const searchMatch =
                    !search
                    || game.title
                        .toLowerCase()
                        .includes(search)
                    || (
                        game.developer
                        || ""
                    )
                        .toLowerCase()
                        .includes(search);

                const genreMatch =
                    !genre
                    || game.genres.some(
                        item =>
                            item.slug
                            === genre
                    );

                return (
                    searchMatch
                    && genreMatch
                );

            }
        );

    if (!games.length) {

        elements.gamesGrid.innerHTML =
            `
                <div class="empty-state">
                    No games match your filters.
                </div>
            `;

        return;
    }

    elements.gamesGrid.innerHTML =
        games.map(
            game => {

                const isOwned =
                    owned.has(
                        game.id
                    );

                return `
                    <article class="game-card">

                        <div class="eyebrow">
                            ${
                                escapeHtml(
                                    game.developer
                                    || "GAMEHUB"
                                )
                            }
                        </div>

                        <h3>
                            ${
                                escapeHtml(
                                    game.title
                                )
                            }
                        </h3>

                        <p>
                            ${
                                escapeHtml(
                                    game.description
                                    || (
                                        "No description "
                                        + "available."
                                    )
                                )
                            }
                        </p>

                        <div class="game-meta">
                            ${
                                game.genres
                                    .map(
                                        item => `
                                            <span
                                                class="tag"
                                            >
                                                ${
                                                    escapeHtml(
                                                        item.name
                                                    )
                                                }
                                            </span>
                                        `
                                    )
                                    .join("")
                            }
                        </div>

                        <div class="game-card-footer">

                            <div>
                                <div class="price">
                                    ${
                                        formatMoney(
                                            game.price
                                        )
                                    }
                                </div>

                                ${
                                    isOwned
                                        ? `
                                            <div
                                                class="owned-label"
                                            >
                                                In library
                                            </div>
                                        `
                                        : ""
                                }
                            </div>

                            <div class="game-actions">

                                <button
                                    class="
                                        button
                                        button-secondary
                                    "
                                    data-action="reviews"
                                    data-game-id="${game.id}"
                                >
                                    Reviews
                                </button>

                                <button
                                    class="
                                        button
                                        button-primary
                                    "
                                    data-action="buy"
                                    data-game-id="${game.id}"
                                    ${
                                        isOwned
                                            ? "disabled"
                                            : ""
                                    }
                                >
                                    ${
                                        isOwned
                                            ? "Owned"
                                            : "Buy"
                                    }
                                </button>

                            </div>

                        </div>

                    </article>
                `;

            }
        )
        .join("");

}


async function buyGame(
    gameId
) {

    if (!state.user) {

        openAuth(
            "login"
        );

        return;
    }

    const game =
        state.games.find(
            item =>
                item.id
                === gameId
        );

    if (
        !window.confirm(
            (
                `Purchase ${
                    game?.title
                    || "this game"
                }?`
            )
        )
    ) {
        return;
    }

    try {

        const {
            data,
            response,
        } = await apiRequest(
            "/api/orders",
            {
                method: "POST",

                body: JSON.stringify({
                    game_id: gameId,
                }),
            }
        );

        const traceId =
            response.headers.get(
                "X-Langfuse-Trace-ID"
            );

        await Promise.all([
            loadLibrary(false),
            loadOrders(false),
            loadNotifications(false),
        ]);

        renderStore();

        toast(
            "Purchase completed",
            "success",
            (
                `${data.game_title}`
                + (
                    traceId
                        ? (
                            " · Trace "
                            + traceId.slice(
                                0,
                                10
                            )
                            + "…"
                        )
                        : ""
                )
            ),
        );

    } catch (error) {

        toast(
            "Purchase failed",
            "error",
            error.message,
        );

    }

}


async function loadLibrary(
    render = true
) {

    if (!state.user) {
        return;
    }

    try {

        const {
            data,
        } = await apiRequest(
            "/api/library"
        );

        state.library = data;

        if (render) {
            renderLibrary();
        }

    } catch (error) {

        toast(
            "Cannot load library",
            "error",
            error.message,
        );

    }

}


function renderLibrary() {

    if (
        !state.library.length
    ) {

        elements.libraryGrid
            .innerHTML =
            `
                <div class="empty-state">
                    Your library is empty.
                    Buy a game from the Store.
                </div>
            `;

        return;
    }

    elements.libraryGrid
        .innerHTML =
        state.library
            .map(
                item => `
                    <article class="game-card">

                        <div class="eyebrow">
                            OWNED
                        </div>

                        <h3>
                            ${
                                escapeHtml(
                                    item.game_title
                                )
                            }
                        </h3>

                        <p>
                            Purchased for
                            ${
                                formatMoney(
                                    item.purchase_price
                                )
                            }.
                        </p>

                        <div class="game-meta">
                            <span class="tag">
                                Order #${item.order_id}
                            </span>

                            <span class="tag">
                                ${
                                    escapeHtml(
                                        formatDate(
                                            item.acquired_at
                                        )
                                    )
                                }
                            </span>
                        </div>

                        <div class="game-card-footer">

                            <span class="owned-label">
                                Ready to play
                            </span>

                            <button
                                class="
                                    button
                                    button-secondary
                                "
                                data-action="reviews"
                                data-game-id="${item.game_id}"
                            >
                                Reviews
                            </button>

                        </div>

                    </article>
                `
            )
            .join("");

}


async function loadOrders(
    render = true
) {

    if (!state.user) {
        return;
    }

    try {

        const {
            data,
        } = await apiRequest(
            "/api/orders"
        );

        state.orders = data;

        if (render) {
            renderOrders();
        }

    } catch (error) {

        toast(
            "Cannot load orders",
            "error",
            error.message,
        );

    }

}


function renderOrders() {

    if (!state.orders.length) {

        elements.ordersContent
            .innerHTML =
            `
                <div class="empty-state">
                    No purchases yet.
                </div>
            `;

        return;
    }

    elements.ordersContent
        .innerHTML = `
            <table class="data-table">

                <thead>
                    <tr>
                        <th>Order</th>
                        <th>Game</th>
                        <th>Price</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>

                <tbody>
                    ${
                        state.orders
                            .map(
                                order => `
                                    <tr>
                                        <td>
                                            #${order.id}
                                        </td>

                                        <td>
                                            ${
                                                escapeHtml(
                                                    order.game_title
                                                )
                                            }
                                        </td>

                                        <td>
                                            ${
                                                formatMoney(
                                                    order.total_price
                                                )
                                            }
                                        </td>

                                        <td>
                                            ${
                                                escapeHtml(
                                                    order.status
                                                )
                                            }
                                        </td>

                                        <td>
                                            ${
                                                escapeHtml(
                                                    formatDate(
                                                        order.created_at
                                                    )
                                                )
                                            }
                                        </td>
                                    </tr>
                                `
                            )
                            .join("")
                    }
                </tbody>

            </table>
        `;

}


async function loadNotifications(
    render = true
) {

    if (!state.user) {
        return;
    }

    try {

        const {
            data,
        } = await apiRequest(
            "/api/notifications"
        );

        state.notifications =
            data;

        updateNotificationBadge();

        if (render) {
            renderNotifications();
        }

    } catch (error) {

        toast(
            "Cannot load notifications",
            "error",
            error.message,
        );

    }

}


function updateNotificationBadge() {

    const unread =
        state.notifications.filter(
            item =>
                !item.is_read
        ).length;

    elements.notificationBadge
        .textContent =
        unread;

    elements.notificationBadge
        .classList.toggle(
            "hidden",
            unread === 0,
        );

}


function renderNotifications() {

    if (
        !state.notifications.length
    ) {

        elements.notificationsList
            .innerHTML =
            `
                <div class="empty-state">
                    No notifications.
                </div>
            `;

        return;
    }

    elements.notificationsList
        .innerHTML =
        state.notifications
            .map(
                item => `
                    <article
                        class="
                            notification-item
                            ${
                                item.is_read
                                    ? ""
                                    : "unread"
                            }
                        "
                    >

                        <div>

                            <h3>
                                ${
                                    escapeHtml(
                                        item.title
                                    )
                                }
                            </h3>

                            <p>
                                ${
                                    escapeHtml(
                                        item.message
                                    )
                                }
                            </p>

                            <div
                                class="notification-time"
                            >
                                ${
                                    escapeHtml(
                                        formatDate(
                                            item.created_at
                                        )
                                    )
                                }
                            </div>

                        </div>

                        ${
                            !item.is_read
                                ? `
                                    <button
                                        class="
                                            button
                                            button-secondary
                                        "
                                        data-action="read-notification"
                                        data-notification-id="${item.id}"
                                    >
                                        Mark read
                                    </button>
                                `
                                : ""
                        }

                    </article>
                `
            )
            .join("");

}


async function markNotificationRead(
    notificationId
) {

    try {

        await apiRequest(
            (
                "/api/notifications/"
                + notificationId
                + "/read"
            ),
            {
                method: "PATCH",
            }
        );

        await loadNotifications();

    } catch (error) {

        toast(
            "Cannot update notification",
            "error",
            error.message,
        );

    }

}


async function loadServices() {

    try {

        const {
            data,
        } = await apiRequest(
            "/services/status"
        );

        state.services =
            data.services;

        renderServices();

    } catch (error) {

        elements.heroStatusText
            .textContent =
            "Gateway unavailable";

        elements.heroStatusDot
            .classList.add(
                "offline"
            );

        toast(
            "Cannot check services",
            "error",
            error.message,
        );

    }

}


function renderServices() {

    const entries =
        Object.entries(
            state.services
        );

    const healthy =
        entries.length === 7
        && entries.every(
            (
                [
                    ,
                    service,
                ]
            ) =>
                service.status
                === "ok"
        );

    elements.heroStatusDot
        .classList.remove(
            "online",
            "offline",
        );

    elements.heroStatusDot
        .classList.add(
            healthy
                ? "online"
                : "offline"
        );

    elements.heroStatusText
        .textContent =
        healthy
            ? "All services operational"
            : "Service degradation";

    elements.servicesGrid
        .innerHTML =
        entries.map(
            (
                [
                    name,
                    service,
                ]
            ) => `
                <article class="service-card">

                    <div class="service-name">
                        ${
                            escapeHtml(
                                name
                            )
                        }
                    </div>

                    <div class="service-url">
                        ${
                            escapeHtml(
                                service.url
                                || ""
                            )
                        }
                    </div>

                    <div
                        class="
                            service-state
                            ${
                                service.status
                                === "ok"
                                    ? "ok"
                                    : "failed"
                            }
                        "
                    >
                        <span>
                            ${
                                service.status
                                === "ok"
                                    ? "●"
                                    : "●"
                            }
                        </span>

                        ${
                            escapeHtml(
                                service.status
                            )
                        }
                    </div>

                </article>
            `
        )
        .join("");

}


async function showReviews(
    gameId
) {

    const game =
        state.games.find(
            item =>
                item.id
                === gameId
        );

    elements.reviewsTitle
        .textContent =
        (
            game?.title
            || "Game reviews"
        );

    elements.reviewsContent
        .innerHTML =
        `
            <div class="empty-state">
                Loading reviews...
            </div>
        `;

    elements.reviewsDialog
        .showModal();

    try {

        const {
            data,
        } = await apiRequest(
            (
                `/api/games/${gameId}`
                + "/reviews"
            )
        );

        renderReviews(
            gameId,
            data,
        );

    } catch (error) {

        elements.reviewsContent
            .innerHTML =
            `
                <div class="empty-state">
                    ${
                        escapeHtml(
                            error.message
                        )
                    }
                </div>
            `;

    }

}


function renderReviews(
    gameId,
    reviews,
) {

    const ownsGame =
        state.library.some(
            item =>
                item.game_id
                === gameId
        );

    const ownReview =
        state.user
            ? reviews.find(
                item =>
                    item.user_id
                    === state.user.id
            )
            : null;

    const list =
        reviews.length
            ? `
                <div class="review-list">

                    ${
                        reviews
                            .map(
                                review => `
                                    <article
                                        class="review-item"
                                    >

                                        <div
                                            class="review-header"
                                        >

                                            <strong>
                                                User
                                                #${review.user_id}
                                            </strong>

                                            <span
                                                class="review-rating"
                                            >
                                                ${
                                                    "★"
                                                        .repeat(
                                                            review.rating
                                                        )
                                                }${
                                                    "☆"
                                                        .repeat(
                                                            5
                                                            - review.rating
                                                        )
                                                }
                                            </span>

                                        </div>

                                        <p>
                                            ${
                                                escapeHtml(
                                                    review.content
                                                )
                                            }
                                        </p>

                                        ${
                                            (
                                                state.user
                                                && review.user_id
                                                === state.user.id
                                            )
                                                ? `
                                                    <div
                                                        class="review-actions"
                                                    >
                                                        <button
                                                            class="
                                                                button
                                                                button-secondary
                                                            "
                                                            data-action="edit-review"
                                                            data-review-id="${review.id}"
                                                            data-game-id="${gameId}"
                                                        >
                                                            Edit
                                                        </button>

                                                        <button
                                                            class="
                                                                button
                                                                button-danger
                                                            "
                                                            data-action="delete-review"
                                                            data-review-id="${review.id}"
                                                            data-game-id="${gameId}"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                `
                                                : ""
                                        }

                                    </article>
                                `
                            )
                            .join("")
                    }

                </div>
            `
            : `
                <div class="empty-state">
                    No reviews yet.
                </div>
            `;

    let form = "";

    if (
        state.user
        && ownsGame
        && !ownReview
    ) {

        form = `
            <form
                id="reviewForm"
                class="review-form"
            >

                <h3>
                    Write a review
                </h3>

                <label>
                    Rating

                    <select
                        id="reviewRating"
                        class="input"
                    >
                        <option value="5">
                            5 - Excellent
                        </option>

                        <option value="4">
                            4 - Good
                        </option>

                        <option value="3">
                            3 - Average
                        </option>

                        <option value="2">
                            2 - Poor
                        </option>

                        <option value="1">
                            1 - Bad
                        </option>
                    </select>
                </label>

                <label>
                    Review

                    <textarea
                        id="reviewContent"
                        class="input textarea"
                        required
                        minlength="3"
                        maxlength="4000"
                    ></textarea>
                </label>

                <button
                    class="button button-primary"
                    type="submit"
                >
                    Publish review
                </button>

            </form>
        `;

    } else if (
        state.user
        && !ownsGame
    ) {

        form = `
            <div class="empty-state">
                Purchase this game to write
                a review from the UI.
            </div>
        `;

    }

    elements.reviewsContent
        .innerHTML =
        list + form;

    const reviewForm =
        document.querySelector(
            "#reviewForm"
        );

    if (reviewForm) {

        reviewForm
            .addEventListener(
                "submit",
                event =>
                    createReview(
                        event,
                        gameId,
                    )
            );

    }

}


async function createReview(
    event,
    gameId,
) {

    event.preventDefault();

    const rating =
        Number(
            document
                .querySelector(
                    "#reviewRating"
                )
                .value
        );

    const content =
        document
            .querySelector(
                "#reviewContent"
            )
            .value
            .trim();

    try {

        await apiRequest(
            (
                `/api/games/${gameId}`
                + "/reviews"
            ),
            {
                method: "POST",

                body: JSON.stringify({
                    rating,
                    content,
                }),
            }
        );

        toast(
            "Review published"
        );

        await loadNotifications(
            false
        );

        await showReviews(
            gameId
        );

    } catch (error) {

        toast(
            "Cannot publish review",
            "error",
            error.message,
        );

    }

}


async function editReview(
    reviewId,
    gameId
) {

    const rating = Number(
        window.prompt(
            "New rating from 1 to 5:",
            "5",
        )
    );

    if (
        !Number.isInteger(
            rating
        )
        || rating < 1
        || rating > 5
    ) {
        return;
    }

    const content =
        window.prompt(
            "New review text:"
        );

    if (!content) {
        return;
    }

    try {

        await apiRequest(
            `/api/reviews/${reviewId}`,
            {
                method: "PATCH",

                body: JSON.stringify({
                    rating,
                    content,
                }),
            }
        );

        toast(
            "Review updated"
        );

        await showReviews(
            gameId
        );

    } catch (error) {

        toast(
            "Cannot update review",
            "error",
            error.message,
        );

    }

}


async function deleteReview(
    reviewId,
    gameId
) {

    if (
        !window.confirm(
            "Delete this review?"
        )
    ) {
        return;
    }

    try {

        await apiRequest(
            `/api/reviews/${reviewId}`,
            {
                method: "DELETE",
            }
        );

        toast(
            "Review deleted"
        );

        await showReviews(
            gameId
        );

    } catch (error) {

        toast(
            "Cannot delete review",
            "error",
            error.message,
        );

    }

}


async function createGenre(
    event
) {

    event.preventDefault();

    const name =
        elements.genreName
            .value
            .trim();

    try {

        await apiRequest(
            "/api/genres",
            {
                method: "POST",

                body: JSON.stringify({
                    name,
                }),
            }
        );

        elements.genreForm
            .reset();

        toast(
            "Genre created"
        );

        await loadGenres();

    } catch (error) {

        toast(
            "Cannot create genre",
            "error",
            error.message,
        );

    }

}


async function createGame(
    event
) {

    event.preventDefault();

    const selectedGenres =
        Array.from(
            elements.gameGenres
                .selectedOptions
        ).map(
            option =>
                Number(
                    option.value
                )
        );

    const releaseDate =
        document.querySelector(
            "#gameReleaseDate"
        ).value;

    const payload = {
        title:
            document.querySelector(
                "#gameTitle"
            ).value.trim(),

        price:
            Number(
                document
                    .querySelector(
                        "#gamePrice"
                    ).value
            ),

        description:
            document.querySelector(
                "#gameDescription"
            ).value.trim()
            || null,

        developer:
            document.querySelector(
                "#gameDeveloper"
            ).value.trim()
            || null,

        publisher:
            document.querySelector(
                "#gamePublisher"
            ).value.trim()
            || null,

        release_date:
            releaseDate
            || null,

        is_published:
            document.querySelector(
                "#gamePublished"
            ).checked,

        genre_ids:
            selectedGenres,
    };

    try {

        await apiRequest(
            "/api/games",
            {
                method: "POST",

                body: JSON.stringify(
                    payload
                ),
            }
        );

        elements.gameForm.reset();

        document.querySelector(
            "#gamePublished"
        ).checked = true;

        toast(
            "Game created"
        );

        await loadGames();

    } catch (error) {

        toast(
            "Cannot create game",
            "error",
            error.message,
        );

    }

}


document
    .querySelectorAll(
        "[data-page]"
    )
    .forEach(
        button => {

            button.addEventListener(
                "click",
                () =>
                    navigate(
                        button.dataset.page
                    )
            );

        }
    );


document
    .querySelector(
        ".brand"
    )
    .addEventListener(
        "click",
        () =>
            navigate(
                "store"
            )
    );


document
    .querySelector(
        "#loginButton"
    )
    .addEventListener(
        "click",
        () =>
            openAuth(
                "login"
            )
    );


document
    .querySelector(
        "#registerButton"
    )
    .addEventListener(
        "click",
        () =>
            openAuth(
                "register"
            )
    );


document
    .querySelector(
        "#logoutButton"
    )
    .addEventListener(
        "click",
        () => {

            clearSession();

            navigate(
                "store"
            );

            toast(
                "Signed out"
            );

        }
    );


document
    .querySelector(
        "#heroLibraryButton"
    )
    .addEventListener(
        "click",
        () =>
            navigate(
                "library"
            )
    );


document
    .querySelector(
        "#closeAuthButton"
    )
    .addEventListener(
        "click",
        () =>
            elements
                .authDialog
                .close()
    );


elements.authModeToggle
    .addEventListener(
        "click",
        () => {

            openAuth(
                state.authMode
                    === "login"
                    ? "register"
                    : "login"
            );

        }
    );


elements.authForm
    .addEventListener(
        "submit",
        handleAuthSubmit
    );


document
    .querySelector(
        "#closeReviewsButton"
    )
    .addEventListener(
        "click",
        () =>
            elements
                .reviewsDialog
                .close()
    );


document
    .querySelector(
        "#refreshGamesButton"
    )
    .addEventListener(
        "click",
        loadGames
    );


document
    .querySelector(
        "#refreshNotificationsButton"
    )
    .addEventListener(
        "click",
        () =>
            loadNotifications()
    );


document
    .querySelector(
        "#refreshServicesButton"
    )
    .addEventListener(
        "click",
        loadServices
    );


elements.gameSearch
    .addEventListener(
        "input",
        renderStore
    );


elements.genreFilter
    .addEventListener(
        "change",
        renderStore
    );


elements.genreForm
    .addEventListener(
        "submit",
        createGenre
    );


elements.gameForm
    .addEventListener(
        "submit",
        createGame
    );


document.body
    .addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    "[data-action]"
                );

            if (!button) {
                return;
            }

            const action =
                button.dataset.action;

            if (
                action === "buy"
            ) {

                buyGame(
                    Number(
                        button.dataset
                            .gameId
                    )
                );

            }

            if (
                action === "reviews"
            ) {

                showReviews(
                    Number(
                        button.dataset
                            .gameId
                    )
                );

            }

            if (
                action
                === "read-notification"
            ) {

                markNotificationRead(
                    Number(
                        button.dataset
                            .notificationId
                    )
                );

            }

            if (
                action === "edit-review"
            ) {

                editReview(
                    Number(
                        button.dataset
                            .reviewId
                    ),
                    Number(
                        button.dataset
                            .gameId
                    ),
                );

            }

            if (
                action === "delete-review"
            ) {

                deleteReview(
                    Number(
                        button.dataset
                            .reviewId
                    ),
                    Number(
                        button.dataset
                            .gameId
                    ),
                );

            }

        }
    );


async function bootstrap() {

    loadStoredSession();

    updateAuthUi();

    await Promise.all([
        loadGames(),
        loadGenres(),
        loadServices(),
    ]);

    await restoreUser();

}


bootstrap();