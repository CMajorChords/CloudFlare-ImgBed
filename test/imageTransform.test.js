import assert from 'node:assert/strict';
import { describe, it } from 'mocha';
import {
    parseImageTransform,
    validateImageTransformRequest,
} from '../functions/file/imageTransform.js';

describe('image transform request handling', () => {
    it('parses an enabled resize request', () => {
        const url = new URL('https://example.com/file/photo.jpg?width=640&height=480&fit=cover');

        assert.deepEqual(
            parseImageTransform(url, { imageTransformEnabled: true }),
            {
                requested: true,
                sizeKey: '640x480',
                fallback: null,
                options: { width: 640, height: 480, fit: 'cover' },
            },
        );
    });

    it('rejects unsafe dimensions and disallowed sizes', () => {
        const oversized = new URL('https://example.com/file/photo.jpg?width=5000');
        const restricted = new URL('https://example.com/file/photo.jpg?width=640&height=480');

        assert.match(
            parseImageTransform(oversized, { imageTransformEnabled: true }).error,
            /between 1 and 4096/,
        );
        assert.match(
            parseImageTransform(restricted, {
                imageTransformEnabled: true,
                imageTransformAllowedSizes: '320x240,800x600',
            }).error,
            /is not allowed/,
        );
    });

    it('rejects range requests when resizing is requested', () => {
        const url = new URL('https://example.com/file/photo.jpg?width=640');
        const imageTransform = parseImageTransform(url, { imageTransformEnabled: true });
        const request = new Request(url, { headers: { Range: 'bytes=0-100' } });

        assert.equal(validateImageTransformRequest(request, imageTransform).status, 400);
    });
});
