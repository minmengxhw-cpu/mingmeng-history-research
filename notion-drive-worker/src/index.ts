import { Worker } from "@notionhq/workers";
import { j } from "@notionhq/workers/schema-builder";

const worker = new Worker();
export default worker;

const googleDriveAuth = worker.oauth("googleDriveAuth", {
	name: "google-drive",
	authorizationEndpoint: "https://accounts.google.com/o/oauth2/v2/auth",
	tokenEndpoint: "https://oauth2.googleapis.com/token",
	scope: "https://www.googleapis.com/auth/drive.metadata.readonly",
	clientId: process.env.GOOGLE_OAUTH_CLIENT_ID ?? "",
	clientSecret: process.env.GOOGLE_OAUTH_CLIENT_SECRET ?? "",
	authorizationParams: {
		access_type: "offline",
		prompt: "consent",
	},
});

worker.tool("checkGoogleDrive", {
	title: "Check Google Drive",
	description: "Checks whether this worker can access the connected Google Drive account.",
	schema: j.object({}),
	execute: async () => {
		const token = await googleDriveAuth.accessToken();
		const response = await fetch(
			"https://www.googleapis.com/drive/v3/about?fields=user,storageQuota",
			{
				headers: {
					Authorization: `Bearer ${token}`,
				},
			},
		);

		if (!response.ok) {
			return {
				ok: false,
				status: response.status,
				body: await response.text(),
				about: null,
			};
		}

		return {
			ok: true,
			status: response.status,
			body: null,
			about: await response.json(),
		};
	},
});
