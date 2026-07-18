import type {
  RoomInvitePreview,
  RoomSnapshot,
  RoundFilters,
  WebwovenApi,
} from "../api/types";

export class RoomController {
  readonly #api: WebwovenApi;

  constructor(api: WebwovenApi) {
    this.#api = api;
  }

  create(filters: RoundFilters): Promise<RoomSnapshot> {
    return this.#api.createRoom(filters);
  }

  invite(code: string): Promise<RoomInvitePreview> {
    return this.#api.getRoomInvite(code);
  }

  join(code: string): Promise<RoomSnapshot> {
    return this.#api.joinRoom(code);
  }

  toggleReady(room: RoomSnapshot): Promise<RoomSnapshot> {
    const player = room.players.find((candidate) => candidate.is_current_guest);
    return this.#api.setRoomReady(room.code, !player?.ready);
  }

  start(room: RoomSnapshot): Promise<RoomSnapshot> {
    return this.#api.startRoom(room.code);
  }

  voteRematch(room: RoomSnapshot, accept: boolean): Promise<RoomSnapshot> {
    return this.#api.voteRoomRematch(room.code, accept);
  }

  get(code: string): Promise<RoomSnapshot> {
    return this.#api.getRoom(code);
  }
}
